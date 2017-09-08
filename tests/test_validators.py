from pizza_client.pizza_proxy import (
    pizzas_validator, toppings_validator, pizza_toppings_validator
)

import pytest


def test_pizzas_validator_no_pizza():
    assert pizzas_validator({'cheeseburger': {'description': ''}}) == \
        ['No pizza found']

def test_pizzas_validator_no_name():
    assert pizzas_validator({'pizza': {'description': 'sfods'}}) == \
        ['Invalid pizza name']

def test_toppings_validator_no_topping():
    assert toppings_validator({'pizza': {'description': ''}}) == \
        ['No topping found']

def test_toppings_validator_no_name():
    assert toppings_validator({'topping': {}}) == \
        ['Invalid topping name']

def test_pizza_toppings_validator_a():
    assert pizza_toppings_validator({'topping': {}}) == \
        ['Invalid topping id']

def test_pizza_toppings_validator_b():
    assert pizza_toppings_validator({'topping_id': 'asdf'}) == \
        ['Invalid topping id']
