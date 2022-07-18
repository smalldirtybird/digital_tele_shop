import os

import requests


def get_authorization_token():
    base_url = 'https://api.moltin.com/'
    path = 'oauth/access_token/'
    url = os.path.join(base_url, path)
    client_id = os.environ['ELASTIC_PATH_CLIENT_ID']
    client_secret = os.environ['ELASTIC_PATH_CLIENT_SECRET']
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


def get_products(elastic_path_auth_token):
    base_url = 'https://api.moltin.com/'
    path = 'v2/products/'
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_details(elastic_path_auth_token, product_id):
    base_url = 'https://api.moltin.com/'
    path = 'v2/products/'
    url = os.path.join(base_url, path, product_id)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_image_link(elastic_path_auth_token, file_id):
    base_url = 'https://api.moltin.com/'
    path = 'v2/files/'
    url = os.path.join(base_url, path, file_id)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def add_product_to_cart(
        elastic_path_auth_token, cart_id, product_id, quantity):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/carts/', str(cart_id), 'items/')
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    payload = {
        'data': {
            'type': 'cart_item',
            'id': product_id,
            'quantity': int(quantity)
            }
        }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart_items(elastic_path_auth_token, cart_id):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/carts/', str(cart_id), 'items/')
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_customers_cart(elastic_path_auth_token, cart_id):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/carts/', str(cart_id))
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def delete_item_from_cart(elastic_path_auth_token, cart_id, product_id):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/carts/', str(cart_id), 'items/', product_id)
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_a_customer(elastic_path_auth_token, email, name):
    base_url = 'https://api.moltin.com/'
    path = 'v2/customers/'
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    payload = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
            }
        }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def get_a_customer(elastic_path_auth_token, customer_id):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/customers/', customer_id)
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']
