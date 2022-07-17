import argparse
import json
import os
import traceback
import urllib
from functools import partial
from textwrap import dedent

import redis
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from elastic_path_api import (add_product_to_cart, get_authorization_token,
                              get_cart_items, get_customers_cart,
                              get_product_details, get_product_image_link,
                              get_products)

_database = None


def get_main_menu_keyboard(chat_id):
    ep_authorization_token = get_authorization_token()
    products = get_products(ep_authorization_token)
    keyboard = []
    for number, product in enumerate(products):
        product_name = product['name']
        product_id = product['id']
        product_button = [InlineKeyboardButton(
            product_name, callback_data=product_id)]
        keyboard.append(product_button)
    keyboard.append([InlineKeyboardButton(
        'View shopping cart',
        callback_data='get_cart_details',
    )])
    return InlineKeyboardMarkup(keyboard)


def start(bot, update):
    chat_id = update['message']['chat']['id']
    update.message.reply_text(
        'Please choose:',
        reply_markup=get_main_menu_keyboard(chat_id),
    )
    return 'HANDLE_MENU'


def button(bot, update):
    query = update.callback_query

    bot.edit_message_text(text="Product id: {}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)


def echo(bot, update):
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return 'ECHO'


def download_image(url, path, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()
    with open(path, 'wb') as file:
        file.write(response.content)


def get_image_extension(url):
    parsed_url = urllib.parse.urlsplit(url, scheme='', allow_fragments=True)
    filepath = urllib.parse.unquote(parsed_url[2],
                                    encoding='utf-8', errors='replace')
    path, extension = os.path.splitext(filepath)
    return extension


def handle_menu(bot, update, image_folder_path):
    query = update.callback_query
    ep_authorization_token = get_authorization_token()
    chat_id = query['message']['chat']['id']
    if query.data == 'get_cart_details':
        cart_items = get_cart_items(ep_authorization_token, chat_id)
        cart_total_info = []
        for item in cart_items:
            product_name = item['name']
            product_description = item['description']
            product_price =\
                item['meta']['display_price']['with_tax']['unit']['formatted']
            quantity_in_cart = item['quantity']
            total_product_price =\
                item['meta']['display_price']['with_tax']['value']['formatted']
            product_details_text = dedent(f"""
            {product_name}
            {product_description}
            {product_price}
            {quantity_in_cart} pieces in cart for {total_product_price}
            """)
            cart_total_info.append(product_details_text)
        cart_info = get_customers_cart(ep_authorization_token, chat_id)
        cart_total_amount = \
            cart_info['meta']['display_price']['with_tax']['formatted']
        cart_total_info.append(f'Total: {cart_total_amount}')
        message_id = query['message']['message_id']
        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
        bot.send_message(
            text='\n'.join(cart_total_info),
            chat_id=chat_id,
            # reply_markup=get_main_menu_keyboard(chat_id),
        )
        return 'HANDLE_MENU'
    else:
        product_id = query.data
        product_name, product_price, product_stock, product_description, \
            product_image_id = get_product_details(
                ep_authorization_token,
                product_id,
            )
        product_image_link = get_product_image_link(
            ep_authorization_token,
            product_image_id,
        )
        image_file_extension = get_image_extension(product_image_link)
        image_filepath = os.path.join(
            image_folder_path,
            f'{product_name}{image_file_extension}',
        )
        download_image(product_image_link, image_filepath)
        items_quantities = [1, 5, 10]
        keyboard = []
        for quantity in items_quantities:
            keyboard.append([InlineKeyboardButton(
                f'Buy {quantity}',
                callback_data=f'{product_id}, {quantity}',
            )])
        keyboard.append([InlineKeyboardButton(
            'Back',
            callback_data='menu_return',
        )])
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_id = query['message']['message_id']
        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
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
    query = update['callback_query']['data']
    chat_id = str(update['callback_query']['message']['chat']['id'])
    if query == 'menu_return':
        bot.send_message(
            text='Please choose:',
            chat_id=chat_id,
            reply_markup=get_main_menu_keyboard(chat_id),
        )
        return 'HANDLE_MENU'
    else:
        ep_authorization_token = get_authorization_token()
        product_id, quantity = query.split(sep=', ')
        add_product_to_cart(
                ep_authorization_token,
                chat_id,
                product_id,
                int(quantity),
            )
    return 'HANDLE_DESCRIPTION'


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
        'ECHO': echo,
        'HANDLE_MENU': partial(
            handle_menu,
            image_folder_path=image_folder_path,
        ),
        'HANDLE_DESCRIPTION': handle_description,
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(traceback.format_exc(err))


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
        handle_users_reply,
        image_folder_path=image_folder,
    )
    dispatcher.add_handler(CallbackQueryHandler(handling_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handling_users_reply))
    dispatcher.add_handler(CommandHandler('start', handling_users_reply))
    updater.start_polling()


if __name__ == '__main__':
    main()
