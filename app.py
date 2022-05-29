import time

import pandas as pd
from flask import Flask, request, json
import requests
from math import sqrt
import pickle
from random import randint
from sklearn.linear_model import LinearRegression
import h3
import asyncio

glat = 0
glon = 0
app = Flask(__name__)
token = "5531224353:AAFfCSK5rBi8xdTRqUgHSkJs-gQWCe67CRQ"
fv = False

loaded_model = pickle.load(open("finalized_model.sav", 'rb'))
amenty = pd.read_csv('data/osm_amenity.csv')
amenty.dropna()
stops = pd.read_csv('data/osm_stops.csv')
stops.dropna()


def generate_vector(lat, lon):
    data = {'lat_h3': lat, "lon_h3": lon, "geo_h3_10": h3.geo_to_h3(lat=lat, lng=lon, resolution=7)}
    data['population'] = 58
    data1 = pd.read_csv('data/rosstat_population_all_cities.csv')
    hex_ind = h3.geo_to_h3(lat=lat, lng=lon, resolution=11)
    l = h3.k_ring(hex_ind, 2)
    data['geo_h3_10'] = hex_ind
    for j in range(len(data1)):
        h2_id = data1['geo_h3_10'][j]
        for k in l:
            if h2_id == k:
                data['population'] += data1['population'][j]
    data_tochki = pd.read_csv('data/osm_amenity.csv')
    data['dist_inter'] = 0
    for i in range(len(data)):
        dist = float("inf")
        for j in range(len(data_tochki)):
            dist = min(dist, sqrt((data_tochki['lat'][j] - data['lat_h3']) ** 2 + (
                    data_tochki['lon'][j] - data['lon_h3']) ** 2))
        data['dist_inter'] = dist
    data_tochki = pd.read_csv('data/osm_stops.csv')
    data['dist_ost'] = 0
    for i in range(len(data)):
        dist = float("inf")
        for j in range(len(data_tochki)):
            dist = min(dist, sqrt((data_tochki['lat'][j] - data['lat_h3']) ** 2 + (
                    data_tochki['lon'][j] - data['lon_h3']) ** 2))
        data['dist_ost'] = dist
    data['cnt_shop'] = 0
    data2 = pd.read_csv('data/osm_amenity.csv')
    for i in range(len(data)):
        h3_id = data['geo_h3_10']
        l = h3.k_ring(h3_id, 3)
        for j in range(len(data2)):
            h2_id = data2['geo_h3_10'][j]
            for k in l:
                t = ['Автозапчасти для иномарок', 'Авторемонт и техобслуживание (СТО)', 'Алкогольные напитки', 'Аптеки',
                     'Банки', 'Быстрое питание', 'Доставка готовых блюд', 'Женская одежда', 'Кафе',
                     'Косметика / Парфюмерия', 'Ногтевые студии', 'Овощи / Фрукты', 'Парикмахерские',
                     'Платёжные терминалы',
                     'Постаматы', 'Продуктовые магазины', 'Пункты выдачи интернет-заказов', 'Рестораны', 'Страхование',
                     'Супермаркеты', 'Цветы', 'Шиномонтаж']
                if h2_id == k:
                    for f in t:
                        if data2[f][j] > 0:
                            data['cnt_shop'] += data2[f][j]

    data['population'] /= 100
    data['cnt_shop'] /= 100
    data['dist_inter'] *= 1000
    data['dist_ost'] *= 1000
    return [[randint(1, 4), data['dist_inter'], data['population'], data['dist_ost'], data['cnt_shop']]]


def regres(data):
    res = loaded_model.predict(data)
    return res


def solve(lat, lon, r):
    max_target = 0
    max_ans = ()
    for i in range(len(amenty)):
        if ((lat - amenty['lat'][i]) ** 2 + (lon - amenty['lon'][i]) ** 2) * 111.134861111 * 1000 <= r:
            a = regres(generate_vector(amenty['lat'][i], amenty['lon'][i]))
            if max_target < a:
                max_target = a
                max_ans = (amenty['lat'][i], amenty['lon'][i])
                return max_ans[0], max_ans[1], max_target


def send_message(chat_id, text):
    method = "sendMessage"

    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


def reply_keyboard(chat_id, text):
    reply_markup = {"keyboard": [[{"request_location": True, "text": "Отправить центр зоны"}]], "resize_keyboard": True,
                    "one_time_keyboard": True}
    data = {'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup)}
    method = "sendMessage"
    url = f"https://api.telegram.org/bot{token}/{method}"
    requests.post(url, data=data)


@app.route("/", methods=["GET", "POST"])
def receive_update():
    global fv, glon, glat

    if request.method == "POST":
        try:
            message = request.json["message"]

            chat_id = message["chat"]["id"]
            if "text" in message.keys():
                text = message['text']
            else:
                text = "null"
            print('location' in message.keys())
            if 'location' in message.keys():
                glat = float(message['location']['latitude'])
                glon = float(message['location']['longitude'])
                send_message(chat_id, "Отправьте радиус зоны в метрах")
                fv = True
            elif text.isdigit() and fv:
                send_message(chat_id, f"Обработка данных...")
                result = solve(glat, glon, int(text))

                send_message(chat_id, f"Оптимальная геопозиция lat={result[0]}, lon={result[1]}")
                send_message(chat_id, f"Ожидаемое количество транзакций {result[2]/10}")
                fv = False
            else:
                if not fv:
                    send_message(chat_id, "Отправьте центр зоны в которой хотите разместить банкомат")
                else:
                    send_message(chat_id, "Отправьте радиус зоны в метрах")
            return {"ok": True}
        except:
            return {"ok": True}


if __name__ == "__main__":
    app.run()
