import argparse
import os
import urllib
from functools import partial
from textwrap import dedent

import redis
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

import elastic_path_api as ep_api

_database = None


def get_main_menu_keyboard(chat_id):
    ep_authorization_token = ep_api.get_authorization_token()
    products = ep_api.get_products(ep_authorization_token)
    keyboard = []
    for number, product in enumerate(products):
        product_name = product['name']
        product_id = product['id']
        keyboard.append([InlineKeyboardButton(
            product_name, callback_data=product_id)])
    keyboard.append([InlineKeyboardButton(
        'View shopping cart', callback_data='display_cart_details')])
    return InlineKeyboardMarkup(keyboard)


def start(bot, update):
    chat_id = update['message']['chat']['id']
    update.message.reply_text(
        'Please choose:',
        reply_markup=get_main_menu_keyboard(chat_id),
    )
    return 'HANDLE_MENU'


def download_image(url, path, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()
    with open(path, 'wb') as file:
        file.write(response.content)


def get_image_extension(url):
    parsed_url = urllib.parse.urlsplit(
        url,
        scheme='',
        allow_fragments=True
    )
    filepath = urllib.parse.unquote(
        parsed_url[2],
        encoding='utf-8',
        errors='replace',
    )
    path, extension = os.path.splitext(filepath)
    return extension


def send_cart_to_customer(bot, chat_id, message_id):
    ep_authorization_token = ep_api.get_authorization_token()
    cart_items = ep_api.get_cart_items(ep_authorization_token, chat_id)
    cart_info = ep_api.get_customers_cart(ep_authorization_token, chat_id)
    cart_total_info = []
    keyboard = [[InlineKeyboardButton(
        'Make a purchase', callback_data='request_email')]]
    for item in cart_items:
        product_name = item['name']
        product_description = item['description']
        product_price = \
            item['meta']['display_price']['with_tax']['unit']['formatted']
        product_quantity = item['quantity']
        product_total_amount = \
            item['meta']['display_price']['with_tax']['value']['formatted']
        product_id = item['id']
        product_details_text = dedent(f"""
                {product_name}
                {product_description}
                {product_price}
                {product_quantity} pieces in cart for {product_total_amount}
                """)
        cart_total_info.append(product_details_text)
        keyboard.append([InlineKeyboardButton(
            f'Remove {product_name} from cart', callback_data=product_id)])
    cart_total_amount = \
        cart_info['meta']['display_price']['with_tax']['formatted']
    cart_total_info.append(f'Total: {cart_total_amount}')
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    keyboard.append([InlineKeyboardButton(
        'Back to menu', callback_data='main_menu_return')])
    bot.send_message(
        text='\n'.join(cart_total_info),
        chat_id=chat_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def handle_menu(bot, update, image_folder_path):
    query = update.callback_query
    chat_id = query['message']['chat']['id']
    message_id = query['message']['message_id']
    if query.data == 'display_cart_details':
        send_cart_to_customer(bot, chat_id, message_id)
        return 'HANDLE_CART'
    else:
        ep_authorization_token = ep_api.get_authorization_token()
        product_id = query.data
        product = ep_api.get_product_details(
            ep_authorization_token, product_id)
        product_name = product['name']
        product_price = \
            product['meta']['display_price']['with_tax']['formatted']
        product_stock = product['meta']['stock']['level']
        product_description = product['description']
        product_image_id = product['relationships']['main_image']['data']['id']
        product_image_link = ep_api.get_product_image_link(
            ep_authorization_token, product_image_id)
        image_file_extension = get_image_extension(product_image_link)
        image_filepath = os.path.join(
            image_folder_path, f'{product_name}{image_file_extension}')
        download_image(product_image_link, image_filepath)
        items_quantities = [1, 5, 10]
        keyboard = []
        for quantity in items_quantities:
            keyboard.append([InlineKeyboardButton(
                f'Buy {quantity}', callback_data=f'{product_id}, {quantity}')])
        keyboard.append([InlineKeyboardButton(
            'Back to menu', callback_data='main_menu_return')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        message = dedent(f'''
            {product_name}\n
            {product_price} per one piece\n
            {product_stock} pieces available on stock\n
            {product_description}''')
        with open(image_filepath, 'rb') as image_file:
            bot.send_photo(
                chat_id,
                image_file,
                caption=message,
                reply_markup=reply_markup,
            )
        os.remove(image_filepath)
        return 'HANDLE_DESCRIPTION'


def handle_description(bot, update):
    query_data = update['callback_query']['data']
    chat_id = update['callback_query']['message']['chat']['id']
    if query_data == 'main_menu_return':
        bot.send_message(
            text='Please choose:',
            chat_id=chat_id,
            reply_markup=get_main_menu_keyboard(chat_id),
        )
        return 'HANDLE_MENU'
    else:
        ep_authorization_token = ep_api.get_authorization_token()
        product_id, quantity = query_data.split(sep=', ')
        ep_api.add_product_to_cart(
                ep_authorization_token,
                chat_id,
                product_id,
                quantity,
            )
    return 'HANDLE_DESCRIPTION'


def handle_waiting_email(bot, update):
    user_reply = update['message']['text']
    chat_id = update['message']['chat']['id']
    username = update['message']['chat']['username']
    ep_authorization_token = ep_api.get_authorization_token()
    customer_account = ep_api.create_a_customer(
        ep_authorization_token,
        user_reply,
        username,
    )
    if 'errors' in customer_account:
        bot.send_message(
            text=dedent(f'''
                    Email {user_reply} is invalid or already in use.
                    Please, try again.
                    '''),
            chat_id=chat_id,
        )
        return 'WAITING_EMAIL'
    if customer_account['data']['id']:
        bot.send_message(
            text=dedent(f'''
                Your order is accepted. Please wait for an email:
                {user_reply}
                '''),
            chat_id=chat_id,
        )
        return 'HANDLE MENU'


def handle_cart(bot, update):
    query_data = update['callback_query']['data']
    chat_id = update['callback_query']['message']['chat']['id']
    message_id = update['callback_query']['message']['message_id']
    if query_data == 'request_email':
        bot.send_message(
            text=dedent('''
            Please send your email
            so that our specialists will contact you
            to complete the purchase
            '''),
            chat_id=chat_id,
        )
        return 'WAITING_EMAIL'
    if query_data == 'main_menu_return':
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        bot.send_message(
            text='Please choose:',
            chat_id=chat_id,
            reply_markup=get_main_menu_keyboard(chat_id),
        )
        return 'HANDLE_MENU'
    else:
        ep_authorization_token = ep_api.get_authorization_token()
        ep_api.delete_item_from_cart(
            ep_authorization_token,
            chat_id,
            query_data,
        )
        send_cart_to_customer(bot, chat_id, message_id)
        return 'HANDLE_CART'


def handle_users_reply(bot, update, image_folder_path):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')
    states_functions = {
        'START': start,
        'HANDLE_MENU': partial(
            handle_menu, image_folder_path=image_folder_path),
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_waiting_email,
    }
    state_handler = states_functions[user_state]
    next_state = state_handler(bot, update)
    db.set(chat_id, next_state)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.environ['DB_PASSWORD']
        database_host = os.environ['DB_HOST']
        database_port = os.environ['DB_PORT']
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password,
        )
    return _database


def get_image_folder_path_arguments():
    parser = argparse.ArgumentParser(
        description='Seafood shop in Telegram.')
    parser.add_argument(
        '-dir', '--directory', default='images/',
        help='Image folder path.')
    args = parser.parse_args()
    return args.directory


def main():
    load_dotenv()
    image_folder = get_image_folder_path_arguments()
    os.makedirs(image_folder, exist_ok=True)
    token = os.environ['TELEGRAM_BOT_TOKEN']
    updater = Updater(token)
    dispatcher = updater.dispatcher
    handling_users_reply = partial(
        handle_users_reply, image_folder_path=image_folder)
    dispatcher.add_handler(CallbackQueryHandler(handling_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handling_users_reply))
    dispatcher.add_handler(CommandHandler('start', handling_users_reply))
    updater.start_polling()


if __name__ == '__main__':
    main()
