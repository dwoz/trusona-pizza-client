describe("Initialize pizza client", function() {

    var onReady;
    var config = {
      'url': 'http://192.168.99.100:8080/',
      'user': 'user@example.com'
    };
    var client = pizzaClient(config);
    var toppingsRegex = /pizzas\/([0-9]+)\/toppings$/;
    var Toppings = [
        {id: 1, name: "Cheese"},
        {id: 2, name: "Pepperoni"},
        {id: 3, name: "Sausage"}
    ];
    var Pizzas = [
        {"id": 1, "name": "Cheese", "description": "A simple yet tasty pie."},
        {"id": 2, "name": "Pepperoni", "description": "The king of all pizzas."},
        {"id": 3, "name": "Sausage", "description": "Just trying to be as good as Pep."}
    ];
    var PizzaToppings = {
        1: Array.from([
            {"id": 1, "pizza_id": 1, "topping_id": 1, "name": "Cheese"}]),
        2: Array.from([
            {"id": 2, "pizza_id": 2, "topping_id": 1, "name": "Cheese"},
            {"id": 3, "pizza_id": 2, "topping_id": 2, "name": "Pepperoni"}
        ]),
        3: Array.from([
            {"id": 4, "pizza_id": 3, "topping_id": 1, "name": "Cheese"},
            {"id": 5, "pizza_id": 3, "topping_id": 3, "name": "Sausage"}
        ])
    };

    beforeAll(function() {
        var getPizzaToppings = function(req, res) {
            var match = toppingsRegex.exec(res.url);
            res.respondWith({
                status: 200,
                statusText: 'HTTP/1.1 200 OK',
                contentType: 'application/json',
                responseText: JSON.stringify(PizzaToppings[match[1]]),
            });
        }
        jasmine.Ajax.install();
        jasmine.Ajax.stubRequest('http://192.168.99.100:8080/toppings').andReturn({
            status: 200,
            statusText: 'HTTP/1.1 200 OK',
            contentType: 'application/json',
            responseText: JSON.stringify(Toppings)
        });
        jasmine.Ajax.stubRequest('http://192.168.99.100:8080/pizzas').andReturn({
            status: 200,
            statusText: 'HTTP/1.1 200 OK',
            contentType: 'application/json',
            responseText: JSON.stringify(Pizzas)
        });
        jasmine.Ajax.stubRequest('http://192.168.99.100:8080/pizzas/1/toppings').andCallFunction(getPizzaToppings);
        jasmine.Ajax.stubRequest('http://192.168.99.100:8080/pizzas/2/toppings').andCallFunction(getPizzaToppings);
        jasmine.Ajax.stubRequest('http://192.168.99.100:8080/pizzas/3/toppings').andCallFunction(getPizzaToppings);
        onReady = spyOn(client, 'onReady').and.callThrough();
        $(document).ready(client.onReady.bind(client));
    });

    afterAll(function() {
        jasmine.Ajax.uninstall();
    });

    describe("Before initialization", function() {
        it("Check pizza client state", function() {
            expect(onReady).not.toHaveBeenCalled();
            expect(pizzaClient.avaliableToppings).toBeFalsy();
            expect(pizzaClient.avaliablePizzas).toBeFalsy();
        });
        it("Check pizza client ui state", function() {
            var pizzaDivs = $('#pizzas div[name=pizza]');
            expect(pizzaDivs.length).toBe(0);
            var pizzaToppings = pizzaDivs.find('div.pizza-toppings > span.badge');
            expect(pizzaToppings.length).toBe(0);
        });
    });

    describe("After initialization", function() {
        beforeAll(function(done) {
            $(document).ready(function() {
            var checkDone = function() {
                var pizzaDivs = $('#pizzas div[name=pizza]');
                var pizzaToppings = pizzaDivs.find('div.pizza-toppings > span.badge');
                if (pizzaDivs.length === 3 && pizzaToppings.length === 5) {
                    //expect(Object.keys(client.availablePizzas).length).toBe(3);
                    done();
                } else {
                    setTimeout(checkDone, 10);
                }
            };
            checkDone();
            });
        });
        it("Client has availableToppings", function() {
            expect(Object.keys(client.availableToppings).length).toBe(3);
        });
        it("Client has availablePizzas", function() {
            expect(Object.keys(client.availableToppings).length).toBe(3);
        });
        it("Client has available pizzas toppings", function() {
            expect(Object.keys(client.availablePizzas[1]["toppings"]).length).toBe(1);
            expect(Object.keys(client.availablePizzas[2]["toppings"]).length).toBe(2);
            expect(Object.keys(client.availablePizzas[3]["toppings"]).length).toBe(2);
        });
    });

    describe("Check Ui", function() {
        it("Clicking toppings tab shows toppings", function() {
            expect($('#toppings-tab').is(':visible')).toBe(false);
            $("a[href*=toppings-tab]").trigger('click');
            expect($('#toppings-tab').is(':visible')).toBe(true);
        });
        it("Clicking pizzas tab shows pizzas", function() {
            expect($('#pizzas-tab').is(':visible')).toBe(false);
            $("a[href*=pizzas-tab]").trigger('click');
            expect($('#pizzas-tab').is(':visible')).toBe(true);
        });
        it("Show and hide add pizza toppings modal", function(done) {
            expect($('#addPizzaToppings').is(':visible')).toBe(false);
            $("div[data-pizza-id=3] span[name=add-pizza-topping]").trigger('click');
            setTimeout(function() {
                expect($('#addPizzaToppings').is(':visible')).toBe(true);
                $('#addPizzaToppings').find('button.close').trigger('click');
                done();
            }, 600);
        });
    });

});
