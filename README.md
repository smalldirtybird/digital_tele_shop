# DigitalTeleShop
![](https://psv4.vkuseraudio.net/s/v1/d/99b8ni6g1W4YbyDNCn6_2b-_qI-Rt9EQ74xgRZv1NYAtNaysGAo78mydxOd_he6aqbpOsONYV-SyAzCu7Mg6AvvFql0qI0uNVC4axBIImeTzlDFi5h2CYw/seafood_shop_demo.gif)
This bot will allow to buy your products directly through Telegram.

## How it works:
The bot connects to your store on [Elastic path](https://www.elasticpath.com/), sends the user a list of available products, adds the desired products to the cart and helps to place an order without leaving the messenger.
You can check the work of the bot on the example of a [Seafood store bot](https://t.me/FishEasilyShopBot).

## How to prepare:
1. Install Python 3.9.13. You can get it from [official website](https://www.python.org/).

2. Install libraries with pip:
```
pip3 install -r requirements.txt
```

3. Create a Telegram bot which will help user to choose and by your products - just send message `/newbot` to [@BotFather](https://telegram.me/BotFather) and follow instructions.
After bot will be created, get token from @BotFather and add to .env file:
```
TELEGRAM_BOT_TOKEN ='your_telegram_bot_token'
```
Put your token instead of value in quotes.

4. Create database on [Redislabs](https://redis.com/). 

5. Add the following lines to .env file:
```
DB_HOST = 'your_database_address'
DB_PORT = 'database_port'
DB_PASSWORD = 'database+password'
```

7. The bot interacts with a store operating on the [Elastic path site](https://www.elasticpath.com/).
If you don't have it, you need to create a store and add products in your [account](https://euwest.cm.elasticpath.com/legacy-catalog).
7. In your [personal account](https://euwest.cm.elasticpath.com) copy the authorization keys `Client ID` and `Client Secret` and add them to .env file:
```
ELASTIC_PATH_CLIENT_ID = 'your_client_id'
ELASTIC_PATH_CLIENT_SECRET = 'your client secret'
```

## How to run:
Bot can be launched from the terminal with the commands: `$ python3 tg_bot.py`

During operation, the bot downloads pictures of goods to send them to the user,
and then deletes them. By default, an `images` folder is created for them in the project's root directory,
but you can specify the download path of your choice with the -dir (or --directory) argument: `$ python3 tg_bot.py -dir my_folder_path`
