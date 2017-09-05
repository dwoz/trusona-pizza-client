import base64
import os
from urllib.parse import urlencode
from flask import Flask, request, session, redirect, url_for, Blueprint
import webargs
import requests
import jwt
import yaml


DEFAULTS = {
    'CLIENT_NAME': 'Trusona Pizza Client - Daniel Wozniak',
    'AUTH_URL': 'https://idp.trusona.com/authorizations/openid',
    'TOKEN_URL': 'https://idp.trusona.com/openid/token',
    'USERINFO_URL':  'https://idp.trusona.com/openid/userinfo',
    'REDIRECT_URI': 'http://trusona-pizza-client.woz.io/oidc/callback',
    'CLIENT_ID': os.environ.get('CLIENT_ID', ''),
    'CLIENT_SECRET': os.environ.get('CLIENT_SECRET', ''),
    'SECRET_KEY': os.environ.get('APP_SECRET',  base64.b64encode(os.urandom(36))),
    'DEBUG': False,
    'AUTH_ENABLED': True,
}


app = Flask(__name__, static_folder='')


def configure(app, paths=['app.yml', '.odic-creds.yml'], defaults=DEFAULTS):
    app.config.update(defaults)
    for path in paths:
        try:
            with open(path, 'r') as fp:
                app.config.update(yaml.safe_load(fp.read()))
        except FileNotFoundError as exc:
            app.logger.warn("Config file not found: %s", path)


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


@app.route('/')
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
  # send_static_file will guess the correct MIME type
  return app.send_static_file(path)


@app.route('/oidc/callback')
def oidc_callback():
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
            'redirect_uri': app.config['REDIRECT_URI'],
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
    session['state'] = base64.b64encode(os.urandom(10))
    session['nonce'] = base64.b64encode(os.urandom(10))
    params = {
        'state': session['state'],
        'response_type': 'code',
        'client_id': app.config['CLIENT_ID'],
        'redirect_uri': app.config['REDIRECT_URI'],
        'scope': 'openid email',
        'nonce': session['nonce'],
    }
    url = "{}?{}".format(app.config['AUTH_URL'], urlencode(params))
    return redirect(url)


@app.route('/logout')
def logout():
    session.clear()
    response = redirect('/')
    response.set_cookie('user', expires=0)
    app.save_session(session, response)
    return response





if __name__ == "__main__":

    configure(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
