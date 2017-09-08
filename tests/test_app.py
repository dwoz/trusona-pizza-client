import json
import re
import requests
from httmock import urlmatch, HTTMock, all_requests
from flask import url_for, session
from .jasmine import Jasmine

import pytest

from pizza_client.app import app

jasmine = Jasmine('https://trusona-pizza-client.woz.io/test.html')

def test_index_no_auth(config, client):
    'index returns 200 when auth not enabled'
    config['AUTH_ENABLED'] = False
    client.get(url_for('index')).status_code == 200


def test_index_needs_registration(config, client):
    'index redirects to registration page when needed'
    config['AUTH_ENABLED'] = True
    config['CLIENT_ID'] = ''
    config['CLIENT_SECRET'] = ''
    res = client.get(url_for('index'), follow_redirects=False)
    assert res.status_code == 302
    assert res.location == 'http://testing.dev:5000/register'


def test_index_redirect_login(config, client):
    'index redirects to login page when needed'
    config['AUTH_ENABLED'] = True
    config['CLIENT_ID'] = 'test-client-id'
    config['CLIENT_SECRET'] = 'test-client-secret'
    res = client.get(url_for('index'), follow_redirects=False)
    assert res.status_code == 302
    assert res.location == 'http://testing.dev:5000/login'


def test_login_redirect(config, client):
    'login redirects to idp'
    config['AUTH_ENABLED'] = True
    config['CLIENT_ID'] = 'test-client-id'
    config['CLIENT_SECRET'] = 'test-client-secret'
    config['AUTH_URL'] ='https://idp.test.dev'
    res = client.get(url_for('login'), follow_redirects=False)
    assert res.status_code == 302
    assert res.location.startswith('https://idp.test.dev')


def test_logout(config, client):
    'login clears session and redirects to idp'
    config['AUTH_ENABLED'] = True
    config['CLIENT_ID'] = 'test-client-id'
    config['CLIENT_SECRET'] = 'test-client-secret'
    config['AUTH_URL'] ='https://idp.test.dev'
    with client.session_transaction() as sess:
        sess['user'] = 'user@example.com'
    res = client.get(url_for('logout'), follow_redirects=False)
    assert res.status_code == 302
    assert res.location.startswith('http://testing.dev:5000/')
    with client.session_transaction() as sess:
        assert 'user' not in sess, sess['user']

@all_requests
def pizza_server(url, request):
    pizza_toppings_re = '^/pizzas/([0-9]+)/toppings$'
    if re.match('^/toppings$', url.path) and request.method == 'GET':
        return {
            'status_code': 200,
            'content': json.dumps([
                {'id': 1, 'name': "Cheese"},
                {'id': 2, 'name': "Pepperoni"},
                {'id': 3, 'name': "Sausage"}
            ]),
        }
    elif re.match('^/pizzas$', url.path) and request.method == 'GET':
        return {
            'status_code': 200,
            'content': json.dumps([
                {"id": 1, "name": "Cheese", "description": "A simple yet tasty pie."},
                {"id": 2, "name": "Pepperoni", "description": "The king of all pizzas."},
                {"id": 3, "name": "Sausage", "description": "Just trying to be as good as Pep."}
            ])
        }
    elif re.match(pizza_toppings_re, url.path) and request.method == 'GET':
        pizza_toppings = {
            '1': [
                {"id": 1, "pizza_id": 1, "topping_id": 1, "name": "Cheese"}
            ],
            '2': [
                {"id": 2, "pizza_id": 2, "topping_id": 1, "name": "Cheese"},
                {"id": 3, "pizza_id": 2, "topping_id": 2, "name": "Pepperoni"}
            ],
            '3': [
                {"id": 4, "pizza_id": 3, "topping_id": 1, "name": "Cheese"},
                {"id": 5, "pizza_id": 3, "topping_id": 3, "name": "Sausage"}
            ]
        }
        m = re.match(pizza_toppings_re, url.path)
        return {
            'status_code': 200,
            'content': json.dumps(pizza_toppings[m.groups()[0]])
        }


class UnexpectedRequest(Exception):
    '''
    Raised when test makes an un-expected http request
    '''


@all_requests
def unexpected_request(url, request):
    raise UnexpectedRequest(url.geturl())


def test_proxy_toppings_get(config, client):
    config['AUTH_ENABLED'] = False
    with HTTMock(pizza_server, unexpected_request):
        res = client.get(url_for('pizza_proxy.toppings'), follow_redirects=False)
        assert res.status_code == 200
        data = json.loads(res.get_data().decode())
        assert len(data) == 3
        assert sorted(data, key=lambda x: x['id'])[0] == {'id': 1, 'name': 'Cheese'}


def test_proxy_pizzas(config, client):
    config['AUTH_ENABLED'] = False
    with HTTMock(pizza_server, unexpected_request):
        res = client.get(url_for('pizza_proxy.pizzas'), follow_redirects=False)
        assert res.status_code == 200
        data = json.loads(res.get_data().decode())
        assert len(data) == 3
        assert sorted(data, key=lambda x: x['id'])[0] == \
             {'description': 'A simple yet tasty pie.', 'id': 1, 'name': 'Cheese'}


def test_proxy_pizza_toppings(config, client):
    config['AUTH_ENABLED'] = False
    with HTTMock(pizza_server, unexpected_request):
        res = client.get('/pizzas/1/toppings', follow_redirects=False)
        assert res.status_code == 200
        data = json.loads(res.get_data().decode())
        assert len(data) == 1
        assert data[0] == {'id': 1, 'name': 'Cheese', 'pizza_id': 1, 'topping_id': 1}
