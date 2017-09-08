'''
The pizza proxy blueprint provies authentication and sanitation of pizza server
requests from the pizza client.
'''
from flask import Blueprint, abort, request, session, jsonify, current_app as app
import requests
from .common import url_root


proxy = Blueprint('pizza_proxy', __name__)


@proxy.before_request
def proxy_before():
    '''
    Require a user when auth is enabled
    '''
    request.user = None
    if 'user' in session:
        request.user = session['user']
    elif app.config['AUTH_ENABLED'] == False:
        request.user = 'user@example.com'
    if not request.user:
        return abort(401)


def proxy_method(url, validator=None):
    if request.method == 'GET':
        app.logger.info("Proxy get request %s", url)
        resp = requests.get(url)
        if resp.status_code != 200:
            app.logger.error(resp.text[:200])
            if app.debug:
                return resp.content, resp.status_code
            abort(500)
        return jsonify(resp.json())
    elif request.method == 'POST':
        data = request.get_json()
        if validator:
            errs = validator(data)
            if errs:
                return jsonify(errs), 422
        app.logger.info("Proxy post request %s %s", url, data)
        resp = requests.post(url, json=data)
        if resp.status_code != 200:
            app.logger.error(
                'Unexpected response status=%s content=%s',
                resp.status_code, resp.text[:200]
            )
            if app.debug:
                return resp.content, resp.status_code
            abort(500)
        return jsonify(resp.json())


def toppings_validator(data):
    'Validate toppings POST data'
    errs = []
    if 'topping' not in data:
        errs.append("No topping found")
    elif 'name' not in data['topping'] or not data['topping']['name']:
        errs.append("Invalid topping name")
    return errs


def pizzas_validator(data):
    'Validate pizzas POST data'
    errs = []
    if 'pizza' not in data:
        errs.append("No pizza found")
    elif 'name' not in data['pizza'] or not data['pizza']['name']:
        errs.append("Invalid pizza name")
    return errs


def pizza_toppings_validator(data):
    'Validate pizza toppings POST data'
    errs = []
    if 'topping_id' not in data or not data['topping_id']:
        errs.append("Invalid topping id")
    else:
        try:
            int(data['topping_id'])
        except ValueError:
            errs.append("Invalid topping id")
    return errs


@proxy.route('/toppings', methods=['GET', 'POST'])
def toppings():
    server_url = app.config.get('PIZZA_SERVER', url_root())
    req_url = '{}/toppings'.format(server_url.rstrip('/'))
    return proxy_method(req_url, toppings_validator)


@proxy.route('/pizzas', methods=['GET', 'POST'])
def pizzas():
    server_url = app.config.get('PIZZA_SERVER', url_root())
    req_url = '{}/pizzas'.format(server_url.rstrip('/'))
    return proxy_method(req_url, pizzas_validator)


@proxy.route('/pizzas/<id>/toppings', methods=['GET', 'POST'])
def pizza_toppings(id):
    server_url = app.config.get('PIZZA_SERVER', url_root())
    req_url = '{}/pizzas/{}/toppings'.format(server_url.rstrip('/'), id)
    return proxy_method(req_url, pizza_toppings_validator)
