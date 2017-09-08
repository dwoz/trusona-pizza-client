if (!Array.from) {
    Array.from = function (object) {
        'use strict';
        return [].slice.call(object);
    };
}
pizzaClient = (function() {
    function sanitizeUrl(url)
    {
        return url.replace(/\/$/, "");
    }
    var _pizzaClient = function(config) {
        this.config = {
           url: '/',
           user: 'user@example.com',
           container: 'pizzaClient',
           endpoints: {
               toppings: '/toppings',
               pizzas: '/pizzas',
               pizzatoppings: '/pizzas/%ID%/toppings',
         }
       }
        if (config !== undefined) {
            this.config['url'] = config['url'];
            this.config['user'] = config['user'];
        };
        this.base_url = sanitizeUrl(this.config.url);
        this.availableToppings = {};
        this.availablePizzas = {};
    };
    _pizzaClient.prototype = {
        // formatted endpoint url.
        'url': function(endpoint, id) {
            if (endpoint === undefined) {
                return this.base_url;
            }
            var url = this.base_url + this.config.endpoints[endpoint];
            if (id === undefined) {
                return url;
            }
            return url.replace(/%ID%/, id);
        },
        'addToppingCb': function(data) {
             var item = $('<option>').attr({'value': data.id}).text(data.name);
             var toppings = $('#toppings');
             toppings.append(item);
             this.updateToppings();
        },
        // returns an Array of toppings
        'addTopping': function(evt) {
            var input = $("#topping");
            if (input.val().trim() == "") {
                this.showMessage("Name required");
                return;
            }
            var data = {'topping': {'name': input.val()}};
            input.val('');
            $.ajax(this.url('toppings'), {
                data : JSON.stringify(data),
                contentType : 'application/json',
                type : 'POST',
                success: this.addToppingCb.bind(this)
            });
        },
        'addPizzaCb': function(data) {
            var pizzas = $("#pizzas");
            var lastRow = pizzas.find('div.row:last');
            if (lastRow.length === 0) {
                lastRow = $('<div>').addClass('row');
                pizzas.append(lastRow);
            }
            if (lastRow.find('div[name=pizza]').length < 2) {
                lastRow.append(this.renderPizza(data));
            } else {
                lastRow = $('<div>').addClass('row');
                lastRow.append(this.renderPizza(data));
                pizzas.append(lastRow);
            }
            if (this.availablePizzas[data.id] === undefined) {
                this.availablePizzas[data.id] = {
                    'id': data.id,
                    'name': data.name,
                    'description': data.description,
                    'toppings': {},
                };
            }
        },
        'addPizza': function() {
            var name = $("#pizza").val().trim();
            if (name == "") {
                this.showMessage("Name required");
                return;
            };
            var description = $("#pizza-description").val().trim();
            var data = {'pizza': {'name': name, 'description': description}};
            $.ajax(this.url('pizzas'), {
                data : JSON.stringify(data),
                contentType : 'application/json',
                type : 'POST',
                success: this.addPizzaCb.bind(this)
            });
            $("#pizza").val('');
            $("#pizza-description").val('');
        },
        'showAddPizzaTopping': function(evt) {
            var pizza_id = evt.data.id;
            var availableToppings = [];
            var pizzaToppingIds = [];
            $.each(this.availableToppings, function(id, data) {
                availableToppings.push(data);
            });
            $.each(this.availablePizzas[pizza_id]['toppings'], function(id, data) {
                pizzaToppingIds.push(data.topping_id);
            });
            var availableToppings = availableToppings.filter(function(x) {
                // true when the available topping is not already a pizza topping
                return pizzaToppingIds.indexOf(x.id) == -1;
            });
            if (availableToppings.length == 0) {
                this.showMessage("No toppings available to add.");
                return;
            }
            var addPizzaToppingsDiv = $('#addPizzaToppings');
            var toppings = addPizzaToppingsDiv.find('select[name=availableToppings]');
            toppings.html('');
            $(availableToppings).each(function(idx, data) {
                var id = data.topping_id; // TODO: Check this
                if (id === undefined) {
                    id = data.id;
                }
                var option = $('<option>').attr({'data-topping-id': id}).text(data.name);
                toppings.append(option);
            });
            addPizzaToppingsDiv.find('button[name=add-pizza-topping]').click(
                evt.data, this.addPizzaToppingSubmit.bind(this)
            );
            addPizzaToppingsDiv.modal('show');
        },
        'showMessage': function(message, kind) {
                var msg = $("#templates div[name=error-message]").clone();
                msg.find('span[name=message]').html(message);
                $('#status-message').html('').append(msg);
        },
        'addPizzaToppingCb': function(data) {
            if (Object.keys(data.errors).length > 0) {
                console.log(data.errors)
                return;
            }
            var pizza_id = data.object.pizza_id;
            var pizzaDiv = $("div[data-pizza-id=" + pizza_id + "]");
            // TODO: Only re-render the updated pizza
            this.updatePizzas();
        },
        'addPizzaToppingSubmit': function(evt) {
            var pizza = evt.data;
            var toppingSelect = $('#addPizzaToppings').find("select[name=availableToppings] option:selected");
            var id = toppingSelect.attr('data-topping-id');
            var post_data = {'topping_id': id};
            var url = this.url('pizzatoppings', pizza.id);
            $("#addPizzaToppings").modal('hide');
            //$.post(url, post_data, this.addPizzaToppingCb.bind(this));
            $.ajax(url, {
                data : JSON.stringify(post_data),
                contentType : 'application/json',
                type : 'POST',
                success: this.addPizzaToppingCb.bind(this)
            });
        },
        'updatePizzaToppings': function(id, div) {
            if (div === undefined) {
                  div = $('[data-pizza-id='+id+']').find('div.pizza-toppings');
            }
            $.get(this.url('pizzatoppings', id), function(data) {
                var pizza = this.availablePizzas[id];
                $.each(data, function(idx, topping) {
                    var span = $('<span>').addClass('badge badge-primary').html(topping.name);
                    div.append([span, ' ']);
                    if (pizza.toppings[topping.topping_id] === undefined) {
                        pizza.toppings[topping.topping_id] = topping;
                    }
                });
            }.bind(this));
        },
        // returns an Array of pizzas
        'listPizzas': function(url) {
            this.url = url
        },
        'togglePizzaInfo': function() {
            console.log('togglePizzaInfo');
            $(this).find('div.panel-body').toggle();
        },
        // Handle successful toppins enpoint response
        'updateToppingsCb': function(data) {
            var toppings = $("#toppings");
            // Remove existing toppings
            toppings.html("");
            // Re-populate toppings list
            $(data).each(function(idx, topping) {
                var item = $('<div>').attr({
                    'topping-id': topping.id,
                    'class': 'badge badge-primary'
                }).text(topping.name);
                // Adding a space required for proper line wrapping.
                toppings.append([item, ' ']);
                if (this.availableToppings[topping.id] === undefined) {
                    this.availableToppings[topping.id] = topping;
                }
            }.bind(this));
        },
        // Update the available toppings
        'updateToppings': function(callback) {
            $.get(this.url('toppings'), this.updateToppingsCb.bind(this));
        },
        // Handle successful pizzas enpoint response
        'updatePizzasCb': function(data) {
            var pizzas = $("#pizzas");
            pizzas.html("");
            var renderPizza = this.renderPizza.bind(this);
            $(data).each(function(idx, pizza) {
                if (this.availablePizzas[pizza.id] === undefined) {
                    this.availablePizzas[pizza.id] = {
                        'id': pizza.id,
                        'name': pizza.name,
                        'description': pizza.description,
                        'toppings': {},
                    };
                }
                var lastRow = pizzas.find('div.row:last');
                if (lastRow.length === 0) {
                    lastRow = $('<div>').addClass('row');
                    pizzas.append(lastRow);
                }
                if (lastRow.find('div[name=pizza]').length < 2) {
                    lastRow.append(renderPizza(pizza));
                } else {
                    lastRow = $('<div>').addClass('row');
                    lastRow.append(renderPizza(pizza));
                    pizzas.append(lastRow);
                }
            }.bind(this));
        },
        'updatePizzas': function(callback) {
            if (callback === undefined) {
                $.get(this.url('pizzas'), this.updatePizzasCb.bind(this));
            } else {
                var updateCb = function(data) {
                    this.updatePizzasCb(data);
                    callback(data);
                };
                $.get(this.url('pizzas'), updateCb.bind(this));
            }
        },
        'renderPizza': function(data) {
            var div = $('#templates').find('div[name=pizza]').clone();
            div.attr({'data-pizza-id': data.id});
            var a = div.find('[name=name]').html(data.name);
            a.click(this.togglePizzaInfo.bind(div));
            div.find('span[name=description]').text(data.description);
            this.updatePizzaToppings(data.id, div.find('.pizza-toppings'));
            div.find('span[name=add-pizza-topping]').click(data, this.showAddPizzaTopping.bind(this));
            return div;
        },
        'onReady': function(evt) {
            var tpl = $('#templates div[name=pizzaClient]');
            $("#pizzaClient").html(tpl.html());
            $("#logout").html(this.config.user);
            $('#add-topping').click(this.addTopping.bind(this));
            $('#add-pizza').click(this.addPizza.bind(this));
            this.updateToppings();
            this.updatePizzas();
        }
    };
    function pizzaClient(config) {
        return new _pizzaClient(config);
    };
    return pizzaClient;
}());
