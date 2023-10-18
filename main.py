from pybit.unified_trading import HTTP
import requests
import time
import json
import datetime

"""
    Функция отправки сообщения в телеграм 

    :param     text: Отправляемый текст сообщения
    :type      text: str.
    :param tg_token: Токен телеграм-бота из BotFather
    :type  tg_token: str.
    :param  user_id: ID пользователя бота
    :type   user_id: int.

"""


def send_msg(text, tg_token, user_id):
    url_req = (
        "https://api.telegram.org/bot"
        + tg_token
        + "/sendMessage"
        + "?chat_id="
        + str(user_id)
        + "&text="
        + text
    )
    requests.get(url_req)


"""
    Функция чтения json-файла

    :param     filename: Название файла
    :type      filename: str.
    
    :returns: dict или list
"""


def json_load(filename):
    with open(filename, "r", encoding="utf8") as read_file:
        result = json.load(read_file)
    return result


"""
    Функция записи в json-файл

    :param     filename: Название файла
    :type      filename: str.
    :param     data: Записываемые данные
    :type      data: list or dict.
  
"""


def json_dump(filename, data):
    with open(filename, "w", encoding="utf8") as write_file:
        json.dump(data, write_file, ensure_ascii=False)


try:
    config = json_load(r"./json/config.json")
except:
    print("Заполните корректно файл с настройками")

token        = config["tg_token"]
user_id      = config["user_id"]
api_key      = config["api_key"]
api_secret   = config["api_secret"]
stop_loss    = config["pos_stop_loss"]


session = HTTP(
    testnet    = False,
    api_key    = api_key,
    api_secret = api_secret,
)


while True:
    
    # Проверкаприбыли открытых ордерок 
    try:
        positions = session.get_positions(category="linear", settleCoin="USDT")[
            "result"
        ]["list"]

        for position in positions:
            coeff = 0
            price = float(
                session.get_tickers(category="linear", symbol=position["symbol"],)[
                    "result"
                ]["list"][0]["lastPrice"]
            )

            side = position["side"]
            entry_price = float(position["avgPrice"])
            
            # Текущий коэффициент прибыли
            if side == "Buy":
                coeff = (1 - entry_price / price) * 100
            else:
                coeff = (1 - price / entry_price) * 100

          # Если коэффициент прибыли превышает стоп-лосс,  то позициях закрывается с оповещением в телеграм
            if coeff < stop_loss * -1:
                session.place_order(
                    category="linear",
                    symbol=position["symbol"],
                    side="Buy" if side == "Sell" else "Sell",
                    orderType="Market",
                    qty=position["size"],
                )

                send_msg(
                    "Закрыта позиция по {}, убыток {} USDT".format(
                        position["symbol"],
                        coeff * float(position["size"]) * entry_price / 100,
                    ), 
                    token, 
                    user_id
                )

            

    except Exception as e:
        send_msg("Ошибка в риск-менеджере позиций: {}".format(str(e)), token, user_id)
