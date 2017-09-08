'''
The main pizza client flask application. The flask app provides authentication
to the pizza client and server.
'''
import base64
import os
from urllib.parse import urlencode
from flask import (
    Flask, g, request, session, redirect, url_for, abort, jsonify, render_template,
    Response,
)
import webargs
import requests
import jwt
import ast
import yaml
import json
from functools import wraps
from werkzeug.contrib.fixers import ProxyFix
from .pizza_proxy import proxy
from .common import url_root, url_for_redirect, user



DEFAULTS = {
    'CLIENT_NAME': 'Trusona Pizza Client - Daniel Wozniak',
    'AUTH_URL': 'https://idp.trusona.com/authorizations/openid',
    'TOKEN_URL': 'https://idp.trusona.com/openid/token',
    'USERINFO_URL':  'https://idp.trusona.com/openid/userinfo',
    'REGISTRATION_URI': 'https://idp.trusona.com/openid/clients',
    'PIZZA_SERVER': 'http://pizza_server:3000',
    'DEBUG': False,
    'USE_PROXY': True,
    'AUTH_ENABLED': True,
    'SECRET_KEY': base64.b64encode(os.urandom(36)),
    'CLIENT_ID': '',
    'CLIENT_SECRET': '',
}
ENV = (
    'CLIENT_ID',
    'CLIENT_SECRET',
    'SECRET_KEY',
    'AUTH_ENABLED',
    'PIZZA_SERVER',
    'USE_PROXY',
)


app = Flask(__name__)
app.register_blueprint(proxy)


def configure(app, paths=['pizza-client.yml', '.oidc-creds.yml'], defaults=DEFAULTS, env=ENV):
    '''
    The main app configuration
    '''
    app.config.update(defaults)
    for path in paths:
        try:
            with open(path, 'r') as fp:
                app.config.update(yaml.safe_load(fp.read()))
        except FileNotFoundError as exc:
            app.logger.warn("Config file not found: %s", path)
    for var in env:
        if var in os.environ:
            # Convert bool literals
            try:
                val = ast.literal_eval(os.environ[var])
            except SyntaxError:
                val = os.environ[var]
            app.config[var] = val
    #print(app.config)


def main():
    '''
    The main app entrypoint
    '''
    print("FROM {}".format(__name__))
    configure(app)
    num_proxies = int(app.config.get('PROXIES', 0))
    if num_proxies > 0:
        ProxyFix(app, num_proxies=num_proxies)
    for x in app.config:
        print("CONFIG {} {}".format(x, repr(app.config[x])))
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)


@app.before_request
def before_request():
    '''
     - Respond to OPTIONS requests
     - Populate the request user
    '''
    app.logger.error(os.environ)
    if request.method == 'OPTIONS':
        return make_response('', 200)
    request.user = None
    if 'user' in session:
        request.user = session['user']
    elif app.config['AUTH_ENABLED'] == False:
        request.user = 'user@example.com'


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    return response


def oidc_required(f):
    '''
    A decorator function which will require authentication to access the endpoint
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config['AUTH_ENABLED'] == False:
            return f(*args, **kwargs)
        elif app.config.get('CLIENT_ID', '') and app.config.get('CLIENT_SECRET', ''):
            return f(*args, **kwargs)
        else:
            app.logger.error("register")
            return redirect('/register')
            return app.send_static_file('register.html')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@oidc_required
def index():
    '''
    Pizza client appliction index page
    '''
    if request.user:
        response = Response(render_template('index.html'))
        response.set_cookie('user', request.user)
        return response
    response = redirect(url_for('login'))
    response.set_cookie('user', expires=0)
    return response


@app.route('/test.html')
def test_html():
    '''
    Pizza client jazmine tests
    '''
    return render_template('test.html')


@app.route('/oidc/callback')
def oidc_callback():
    '''
    Handle the odic login redirect
    '''
    if 'error' in request.args:
        return 'Auth error: {}'.format(request.args['error']), 200
    elif 'code' in request.args:
        code = request.args['code']
        req_nonce = request.args['nonce'].encode('utf-8')
        req_state = request.args['state'].encode('utf-8')
        session_nonce = session.pop('nonce', '')
        session_state = session.pop('state', '')
        session.clear()
        if req_nonce != session_nonce or req_state != session_state:
            app.logger.error("req_nonce %s", repr(req_nonce))
            app.logger.error("session_nonce %s", repr(session_nonce))
            app.logger.error("req_state %s", repr(req_state))
            app.logger.error("session_state %s", repr(session_state))
            return 'Invalid authentication state', 200
        data = {
            'code': code,
            'state': req_nonce,
            'nonce': req_state,
            'client_id': app.config['CLIENT_ID'],
            'client_secret': app.config['CLIENT_SECRET'],
            'redirect_uri': url_for_redirect(),
            'grant_type': 'authorization_code',
        }
        resp = requests.post(app.config['TOKEN_URL'], params=data)
        if resp.status_code != 201:
            app.logger.error(
                "Error from token url: %s %s",
                resp.status_code, resp.text[:300]
            )
            return 'Something went wrong', 200
        token_data = resp.json()
        jwtdata = token_data['id_token']
        try:
            id_token = jwt.decode(
                jwtdata, key=app.config['CLIENT_SECRET'], audience=app.config['CLIENT_ID'])
        except jwt.InvalidTokenError as exc:
            app.logger.error("Invalid token")
            return 'invalid jwt token', 200
        session['id_token'] = id_token
        session['user'] = user(session)
        # headers = {
        #     'Authorization': '{} {}'.format(token_data['token_type'], token_data['access_token'])
        # }
        # response = requests.get(USERINFO_URL, headers=headers)
        # app.logger.warn("userinfo status: %s", response.status_code)
        # app.logger.warn("userinfo data: %s", response.json())
        return redirect('/')
    else:
        return 'bad request', 422


@app.route('/login')
def login():
    '''
    Start the oidc login process
    '''
    session['state'] = base64.b64encode(os.urandom(10))
    session['nonce'] = base64.b64encode(os.urandom(10))
    params = {
        'state': session['state'],
        'response_type': 'code',
        'client_id': app.config['CLIENT_ID'],
        'redirect_uri': url_for_redirect(),
        'scope': 'openid email',
        'nonce': session['nonce'],
    }
    url = "{}?{}".format(app.config['AUTH_URL'], urlencode(params))
    return redirect(url)


@app.route('/logout')
def logout():
    '''
    Logout the current user
    '''
    session.clear()
    response = redirect('/')
    response.set_cookie('user', expires=0)
    app.save_session(session, response)
    return response


@app.route('/config.json')
def config_json():
    '''
    Render the current javascript app config as json
    '''
    app.logger.warn("CONFIG %s", app.config)
    if app.config['AUTH_ENABLED']:
        if not session.get('user', ''):
            return abort(401)
    server_url = app.config.get('PIZZA_SERVER', url_root())
    if app.config['USE_PROXY']:
        server_url = url_root()
    config = {
        'user': session.get('user', 'user@examplecom'),
        'pizza_server_url': server_url,
    }
    return jsonify(config)


@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Register this pizza client with the trusona idp. Persist the credentials in
    a file (.oidc-creds.yml)
    '''
    if request.method == 'GET':
        return render_template('register.html')
    if app.config.get('CLIENT_ID', '') and app.config.get('CLIENT_SECRET', ''):
        return 'invalid request', 422
    client_identifier = "{}@{}".format(os.getlogin(), os.uname().nodename)
    client_data = {
        'client_name': 'Trusona Pizza Client - Daniel Wozniak - {}'.format(client_identifier),
        'redirect_uris': [],
    }
    client_data['redirect_uris'].append(url_for_redirect('http'))
    client_data['redirect_uris'].append(url_for_redirect('https'))
    headers={
        'Content-Type': 'application/json'
    }
    response = requests.post(
        app.config['REGISTRATION_URI'], data=json.dumps(client_data), headers=headers
    )
    if response.status_code != 201:
        app.error("Something went wrong: %s", response.text[:300])
        return response.text, 500
    app.logger.info("Got json reponse: %s", response.json())
    data = {
        'CLIENT_NAME': response.json()['client_name'],
        'CLIENT_ID': response.json()['client_id'],
        'CLIENT_SECRET': response.json()['client_secret']
    }
    with open('.oidc-creds.yml', 'w') as fp:
        fp.write(yaml.dump(data, default_flow_style=False))
    app.config.update(data)
    return redirect('/')
