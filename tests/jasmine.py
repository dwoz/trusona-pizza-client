import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from contextlib import contextmanager
import signal
import pytest
from py._path.local import FSBase


def driver_class(name="chrome"):
    mod = getattr(webdriver, name, None)
    if not mod:
        raise Exception
    return mod.webdriver.WebDriver


@contextmanager
def driver_ctx(name="chrome", **kwargs):
    cls = driver_class(name)
    driver = cls(**kwargs)
    driver.set_window_size(1400, 1000)
    yield driver
    driver.close()
    import signal
    driver.service.process.send_signal(signal.SIGKILL)
    driver.quit()


def wait_for_results(driver):
    #WebDriverWait(driver, 100).until(
    #    lambda driver:
    #    driver.execute_script("return document.readyState === 'complete';")
    #)
    WebDriverWait(driver, 100).until(
        lambda driver:
        driver.execute_script("return jsApiReporter.finished;")
    )


def results(driver):
    batch_size = 10
    spec_results = []
    index = 0
    while True:
        results = driver.execute_script(
            "return jsApiReporter.specResults({0}, {1})".format(
                index,
                batch_size
            )
        )
        spec_results.extend(results)
        index += len(results)

        if not len(results) == batch_size:
            break
    return spec_results


class JasmineException(Exception): pass


class Jasmine(object):
    def __init__(self, url=None):
        self.url = url


class JasmineItem(pytest.Item):

    def __init__(self, name, parent, spec):
        super(JasmineItem, self).__init__(name, parent)
        self.spec = spec
        #self._location = (parent.url, None, name)

    def runtest(self):
        assert self.spec['status'] == 'passed'

    def repr_failure(self, excinfo):
        lines = []
        for exp in self.spec['failedExpectations']:
            lines.append(exp['message'])
            #lines.append(exp['stack'])
        return '\n'.join(lines)

    @property
    def originalname(self):
        return 'asdfsd'

    def _getfailureheadline(self, rep):
        return 'mmmm'
        if hasattr(rep, 'location'):
            fspath, lineno, domain = rep.location
            return domain
        else:
            return "test session"  # XXX?

    @property
    def location(self):
        #print("LOCTION CALL")
        return self._location



class JasmineCollector(pytest.Collector):

    def __init__(self, url, *args, **kwargs):
        self.url = url
        self._nodeid = url
        super(JasmineCollector, self).__init__(url, *args, **kwargs)

    def collect(self):
        items = []
#        print("Begin Jasmine collection: {}".format(self.url))
        #with driver_ctx('phantomjs', service_args=["--debug=yes","--remote-debugger-port=9000"]) as driver:
        with driver_ctx('phantomjs', service_args=['--debug=yes']) as driver:
            driver.get(self.url)
            wait_for_results(driver)
            for i in results(driver):
                items.append(JasmineItem(i['description'], self, i))
        return items

    def reportinfo(self):
        return ('.', False, "")
class JasminePath(FSBase):

    def __init__(self, path, expanduser=False):
        self.strpath = path

    def replace(self, *args):
        return self.strpath

    def __repr__(self):
        return self.strpath

    def alt_join(self, *args):
        path = self.strpath
        for i in args:
            path = "{}/{}".format(path.rstrip('/'), i.lstrip('/'))
        o = object.__new__(self.__class__)
        o.strpath = path
        return o
