'''
Config and fixtures for pytest
'''
from pizza_client.app import app

import pytest
import sys
from .jasmine import Jasmine, JasmineCollector, JasmineItem, JasminePath


NOOP = object()


def pytest_addoption(parser):
    parser.addoption(
        "--with-jasmine",
        #action='store_true',
        default=NOOP,
        nargs='?',
        help='Run cassandra tests',
    )


def pytest_pycollect_makeitem(collector, name, obj):
    url = pytest.config.option.with_jasmine
    if url != NOOP and isinstance(obj, Jasmine):
        if url is None:
            url = obj.url
        return JasmineCollector(url, parent=collector.parent)


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if isinstance(item, JasmineItem):
            if config.option.verbose == 1:
                name = JasminePath(item.parent.url)
            else:
                config.rootdir.join = JasminePath.alt_join.__get__(
                    config.rootdir, config.rootdir.__class__
                )
                name = JasminePath(item.name)
            item._location = (name, None, item.name)


@pytest.fixture
def client():
    app.config.update(
        SERVER_NAME='testing.dev:5000',
        SECRET_KEY='secret',
        USE_PROXY=True,
    )
    app.testing = True
    client = app.test_client()
    with app.app_context() as ctx:
        yield client


@pytest.fixture
def config():
    return app.config
