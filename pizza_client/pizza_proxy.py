'''
The pizza proxy blueprint provies authentication and sanitation of pizza server
requests from the pizza client.
'''
from flask import Blueprint, request, session, jsonify, current_app as app
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


def proxy_method(url):
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


@proxy.route('/toppings', methods=['GET', 'POST'])
def toppings():
    server_url = app.config.get('PIZZA_SERVER', url_root())
    req_url = '{}/toppings'.format(server_url.rstrip('/'))
    return proxy_method(req_url)


@proxy.route('/pizzas', methods=['GET', 'POST'])
def pizzas():
    server_url = app.config.get('PIZZA_SERVER', url_root())
    req_url = '{}/pizzas'.format(server_url.rstrip('/'))
    return proxy_method(req_url)


@proxy.route('/pizzas/<id>/toppings', methods=['GET', 'POST'])
def pizza_toppings(id):
    server_url = app.config.get('PIZZA_SERVER', url_root())
    req_url = '{}/pizzas/{}/toppings'.format(server_url.rstrip('/'), id)
    return proxy_method(req_url)
