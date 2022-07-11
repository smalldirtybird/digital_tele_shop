import os
from pprint import pprint

from dotenv import load_dotenv
import requests


def get_elastic_path_authorization_token(client_id, client_secret):
    base_url = 'https://api.moltin.com/'
    path = 'oauth/access_token/'
    url = os.path.join(base_url, path)
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


def get_elastic_path_products(elastic_path_auth_token):
    base_url = 'https://api.moltin.com/'
    path = 'v2/products/'
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def add_product_to_cart(elastic_path_auth_token, cart_name, product_id):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/carts/', cart_name, 'items/')
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    payload = {
        'data': {
            'type': 'cart_item',
            'id': product_id,
            'quantity': 1
            }
        }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart_items(elastic_path_auth_token, cart_name):
    base_url = 'https://api.moltin.com/'
    path = os.path.join('v2/carts/', cart_name, 'items/')
    url = os.path.join(base_url, path)
    headers = {'Authorization': f'Bearer {elastic_path_auth_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def main():
    load_dotenv()
    client_id = os.environ['ELASTIC_PATH_CLIENT_ID']
    client_secret = os.environ['ELASTIC_PATH_CLIENT_SECRET']
    elastic_path_auth_token = get_elastic_path_authorization_token(
        client_id,
        client_secret,
    )
    # print(elastic_path_auth_token)
    # pprint(get_elastic_path_products(elastic_path_auth_token))
    pprint(add_product_to_cart(
        elastic_path_auth_token,
        'test_cart_2',
        '91d918d1-f992-4c28-9149-6c7daa965c9c'
    ))
    pprint(get_cart_items(elastic_path_auth_token, 'test_cart_2'))


if __name__ == '__main__':
    main()
