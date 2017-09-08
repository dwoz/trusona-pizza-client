# [Trusona Pizza Client](https://trusona-pizza-client.woz.io)


1. [Pizza Client](#pizza-client)
    1. [Technology](#technology)
    2. [Repository Layout](#repository-layout)
2. [Run Locally](#running-pizza-client-locally)
3. [Develop Locally](#develop-locally)
    1. [Setting up a python virtual environment](#setting-up-a-python-virtual-environment)
    2. [Running the app](#running-the-app)
    3. [Running the tests](#running-the-tests)
      * [Python tests](#python-tests)
      * [Javascript tests](#javascript-tests)

## Pizza Client

Visit [trusona-pizza-client.woz.io](https://trusona-pizza-client.woz.io) for a
working deployment of this repository. You will need to authenticate using the
Trusona identity provider before accessing the application. Browser based
javascript tests are available at the
[test.html](https://trusona-pizza-client.woz.io/test.html) page.


### Technology

The primary pizza client is implimented in html and javascript using bootstrap
and jquery. There is an additional server application implimented in python
which provides authentication to the Trusona IdP. The server can proxie
requests to the pizza server. When the server acts as a proxie it will also
validate requests before passing them to the server.

When using docker, the default configuration is to have ha-proxy serving up the
pizza_client. In this configuration all pizza server requests go through the
client. See the [haproxy.cfg](pizza_client/extra/haproxy.cfg) file for more
details.

### Repository Layout

- The python code is located in the [pizza_client/](https://github.com/dwoz/trusona-pizza-client/tree/master/pizza_client) directory.
- Python py.test tests are under the [tests/](https://github.com/dwoz/trusona-pizza-client/tree/master/tests) directory
- The code for the client side javascript app is in the [pizza_client/static/pizzaClient.js](https://github.com/dwoz/trusona-pizza-client/blob/master/pizza_client/static/pizzaClient.js) file.
- The javascript app uses html templates, these templates are located in the main layout temlate [layout.html](https://github.com/dwoz/trusona-pizza-client/blob/master/pizza_client/templates/layout.html)
- The Jasmin javascript test suite can be found in the [pizza_client/static/testPizzaClient.js](https://github.com/dwoz/trusona-pizza-client/blob/master/pizza_client/static/pizzaClient.js) file

## Running Pizza Client Locally

Running the Pizza Client on your local machine should be simple. Before trying
to run the pizza client dockere locallaly you will need docker installed.
Please visist the docker website for the installation instructions for your os.

When you have Docker installed you are ready to run the Pizza Client. First,
make a recursive clone of this repository. Then in the root the clone run the
'make run' command to build. This will run the pizza server and client on your
local docker (or docker-machine). The resulting docker network exposes port
8080.


```bash
git clone --recursive git@github.com:dwoz/trusona-pizza-client.git
cd trusona-pizza-client
make run
```


## Develop Locally

It may be handy to run the pizza client app without docker. You should be able to run the app in a python virutal environment provided you have python3 installed. You can install python3 via homebrew `homebrew install python3`.

### Setting up a python virtual environment

```bash
git clone --recursive git@github.com:dwoz/trusona-pizza-client.git
cd trusona-pizza-client
virtualenv venv --python=python3
source venv/bin/activate
pip install -r requirements.txt
python setup.py develop
```

### Running the app

You'll need to make sure the virutal environment is activated. If following the steps above you'll already have an activated virtual environment. If you open a new shell, you'll need to `source venv/bin/activate` before running the app.

```bash
source venv/bin/activate
pizza-client
```

### Running the tests

There are two test suites; a python based test suite and javascript tests.

#### Python tests

```bash
py.test -v
```

#### Javascript tests

You can run the Jasmine javascript tests in your browser by visiting the '/test.html' page of the app.

Alternatively, you can install phantomjs and run the javascript tests along side the python tests.

```bash
brew install phantomjs
py.test -v --with-jasmine=http://192.168.99.100:8080/test.html
```
