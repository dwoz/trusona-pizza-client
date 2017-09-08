from functools import wraps
from flask import request, session, current_app as app
from urllib.parse import urlencode, urlparse, ParseResult


def oidc_required(f):
    '''
    A decorator function which will require authentication to access the endpoint
    '''
    @wraps(f)
    def wrapper_function(*args, **kwargs):
        if app.config['AUTH_ENABLED'] == False:
            return f(*args, **kwargs)
        elif app.config.get('CLIENT_ID', '') and app.config.get('CLIENT_SECRET', ''):
            return f(*args, **kwargs)
        elif do_redirect:
            return redirect('/register')
        else:
            return abort(401)
        return f(*args, **kwargs)
    return wrapper_function


def js_config():
    '''
    build the javascript config object for the request
    '''
    server_url = app.config.get('PIZZA_SERVER', url_root())
    if app.config['USE_PROXY']:
        server_url = url_root()
    config = {
        'url': server_url,
        'user': session.get('user', 'user@examplecom'),
    }
    return config


def url_root(scheme=None):
    '''
    Similar to Flask's url_root but accounts for X-Forwarded-Proto header.
    '''
    p = urlparse(request.url_root)
    if scheme is None:
        if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
            scheme = 'https'
        else:
            scheme = p.scheme
    return ParseResult(
        scheme, p.netloc, p.path, p.params, p.query, p.fragment
    ).geturl()


def url_for_redirect(scheme=None):
    '''
    Create an oidc redirect url for this pizza client
    '''
    p = urlparse(url_root(scheme))
    return ParseResult(
        p.scheme, p.netloc, '/oidc/callback', p.params, p.query, p.fragment
    ).geturl()


def user(session):
    '''
    Extract the user from the session info
    '''
    # TODO: Where does the extra quoting come from ?
    return session['id_token']['emails'][0].strip('"')
