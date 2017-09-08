# [Trusona Pizza Client](https://trusona-pizza-client.woz.io)
1. [Pizza Client](#pizza-client)
    1. [Technology](#technology)
2. [Run Locally](#running-pizza-client-locally)
3. [Develop Locally](#develop-locally)


## Pizza Client

Visit [trusona-pizza-client.woz.io](https://trusona-pizza-client.woz.io) for a working deployment of this repository. You will need to authenticate using the Trusona identity provider before accessing the application. Browser based javascript tests are available at the [test.html](https://trusona-pizza-client.woz.io/test.html) page.

### Technology

The primary pizza client is implimented in html and javascript using bootstrap and jquery. There is an additional server application implimented in python which provides authentication to the Trusona IdP. The server can proxie requests to the pizza server. When the server acts as a proxie it will also validate requests before passing them to the server.

When using docker, the default configuration is to have ha-proxy serving up the pizza_client. In this configuration all pizza server requests go through the client. See the [haproxy.cfg](pizza_client/extra/haproxy.cfg) file for more details.

## Running Pizza Client Locally

Running the Pizza Client on your local machine should be simple. First, clone a copy of this repository. Then in the root the clone run the 'make run' command to build. This will run the pizza server and client on your local docker (or docker-machine). The resulting docker network exposes port 8080.

## Develop Locally

Jasmine tests are available via the '/test.html' page.
