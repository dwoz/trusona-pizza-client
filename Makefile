#!/usr/bin/make -f

#SHELL = bash
.PHONY: all run rund clean build insall-jasmine uninstall-jasmine

#
# Docker machine environment
#

# Create a make file of the docker-machine environment, including .env here aswell
IGNORE := $(shell bash -c "if which docker-machine; then\
	docker-machine env > .docker-machine.mk; \
	env -i bash -c \"source .docker-machine.mk; \
        source .env; env | \
	sed 's/=/:=/' | sed 's/^/export /' > .docker-machine.mk;\"; \
        fi")
-include .docker-machine.mk

DOCKER_MACHINE_NAME := $(DOCKER_MACHINE_NAME)
DOCKER_TLS_VERIFY := $(DOCKER_TLS_VERIFY)
PWD := $(PWD)
DOCKER_CERT_PATH := $(DOCKER_CERT_PATH)
SHLVL := $(SHLVL)



main: build

run: build
	docker-compose up

rund: build
	docker-compose up -d

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	python setup.py clean
	docker-compose rm -f;

build: clean
	docker-compose build

install-jasmine:
	curl -sSL -o jasmine-standalone-2.8.0.zip https://github.com/jasmine/jasmine/releases/download/v2.8.0/jasmine-standalone-2.8.0.zip
	mkdir -p pizza_client/static/jasmine
	unzip jasmine-standalone-2.8.0.zip -d pizza_client/static/jasmine
	rm jasmine-standalone-2.8.0.zip
	curl -sSL -o pizza_client/static/jasmine/mock-ajax.js https://raw.githubusercontent.com/jasmine/jasmine-ajax/v3.3.1/lib/mock-ajax.js

uninstall-jasmine:
	rm -rf pizza_client/static/jasmine
