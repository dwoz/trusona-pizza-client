from flask import request
from urllib.parse import urlencode, urlparse, ParseResult

def url_root(scheme=None):
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
    'Extract the user from the session info'
    # TODO: Where does the extra quoting come from ?
    return session['id_token']['emails'][0].strip('"')


