import base64
import os
from urllib.parse import urlencode, urlparse, ParseResult
from flask import Flask, request, session, redirect, url_for, Blueprint, abort
import webargs
import requests
import jwt
import yaml
import json
from functools import wraps
from flask import g, request, redirect, url_for


DEFAULTS = {
    'CLIENT_NAME': 'Trusona Pizza Client - Daniel Wozniak',
    'AUTH_URL': 'https://idp.trusona.com/authorizations/openid',
    'TOKEN_URL': 'https://idp.trusona.com/openid/token',
    'USERINFO_URL':  'https://idp.trusona.com/openid/userinfo',
    #'REDIRECT_URI': 'http://trusona-pizza-client.woz.io/oidc/callback',
    'REGISTRATION_URI': 'https://idp.trusona.com/openid/clients',
    'CLIENT_ID': os.environ.get('CLIENT_ID', ''),
    'CLIENT_SECRET': os.environ.get('CLIENT_SECRET', ''),
    'SECRET_KEY': os.environ.get('APP_SECRET',  base64.b64encode(os.urandom(36))),
    'DEBUG': False,
    'AUTH_ENABLED': True,
}


app = Flask(__name__, static_folder='')


def configure(app, paths=['app.yml', '.oidc-creds.yml'], defaults=DEFAULTS):
    app.config.update(defaults)
    for path in paths:
        try:
            with open(path, 'r') as fp:
                app.config.update(yaml.safe_load(fp.read()))
        except FileNotFoundError as exc:
            app.logger.warn("Config file not found: %s", path)


def url_for_redirect(scheme=None):
    '''
    Create an oidc redirect url for this pizza client
    '''
    p = urlparse(request.url_root)
    if scheme is None:
        scheme = p.scheme
    return ParseResult(
        scheme, p.netloc, '/oidc/callback', p.params, p.query, p.fragment
    ).geturl()


def user(session):
    'Extract the user from the session info'
    # TODO: Where does the extra quoting come from ?
    return session['id_token']['emails'][0].strip('"')


@app.before_request
def before_request():
    request.user = None
    if 'id_token' in session:
        request.user = user(session)
    elif app.config['AUTH_ENABLED'] == False:
        request.user = 'user@example.com'


def oidc_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config['AUTH_ENABLED'] == False:
            return f(*args, **kwargs)
        elif app.config.get('CLIENT_ID', '') and app.config.get('CLIENT_SECRET', ''):
            return f(*args, **kwargs)
        else:
            return app.send_static_file('register.html')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@oidc_required
def index():
    if request.user:
        response = app.send_static_file('index.html')
        response.set_cookie('user', request.user)
        return response
    response = redirect(url_for('login'))
    response.set_cookie('user', expires=0)
    return response


@app.route('/<path:path>')
def static_proxy(path):
    if path.rsplit('.', 1)[-1] not in ['html', 'js', 'css']:
        return abort(404)
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


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


@app.route('/register', methods=['POST'])
def register():
    '''
    Register this pizza client with the trusona idp. Persist the credentials in
    a file (.oidc-creds.yml)
    '''
    if app.config.get('CLIENT_ID', '') and app.config.get('CLIENT_SECRET', ''):
        return 'invalid request', 422
    p = urlparse(request.url_root)
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


if __name__ == "__main__":
    configure(app)
    app.run(host="0.0.0.0", port=5000, debug=True)