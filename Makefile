
# Create a make file of the docker-machine environment
IGNORE := $(shell bash -c "docker-machine env > .env.mk; source .env.mk; env | sed 's/=/:=/' | sed 's/^/export /' > .env.mk")
-include .env.mk

all: clean build
	docker-compose up

clean:
	docker-compose rm -f;

build:
	docker-compose build

install-jasmine:
	curl -sSL -o jasmine-standalone-2.8.0.zip https://github.com/jasmine/jasmine/releases/download/v2.8.0/jasmine-standalone-2.8.0.zip
	mkdir -p pizza_client/static/jasmine
	unzip jasmine-standalone-2.8.0.zip -d pizza_client/static/jasmine
	rm jasmine-standalone-2.8.0.zip
	curl -sSL -o pizza_client/static/jasmine/mock-ajax.js https://raw.githubusercontent.com/jasmine/jasmine-ajax/v3.3.1/lib/mock-ajax.js

uninstall-jasmine:
	rm -rf pizza_client/static/jasmine
