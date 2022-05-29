from math import sqrt
import pandas as pd
import h3
from sklearn.linear_model import LinearRegression
import pickle

data = pd.read_csv(
    'data/target_hakaton_spb.csv',
    encoding='windows-1251',sep=';')
data1 = pd.read_csv('data/rosstat_population_all_cities.csv')
data['population'] = 0
for i in range(len(data)):
    h3_id = data['geo_h3_10'][i]
    l = h3.k_ring(h3_id, 2)
    for j in range(len(data1)):
        h2_id = data1['geo_h3_10'][j]
        for k in l:
            if h2_id == k:
                data['population'][i] += data1['population'][j]
data_tochki = pd.read_csv('data/osm_amenity.csv')
data['dist_inter'] = 0
for i in range(len(data)):
    dist = float("inf")
    for j in range(len(data_tochki)):
        dist = min(dist, sqrt((data_tochki['lat'][j] - data['lat_h3'][i]) ** 2 + (
                data_tochki['lon'][j] - data['lon_h3'][i]) ** 2))
    data['dist_inter'][i] = dist

data_tochki = pd.read_csv('data/osm_stops.csv')
data['dist_ost'] = 0
for i in range(len(data)):
    dist = float("inf")
    for j in range(len(data_tochki)):
        dist = min(dist, sqrt((data_tochki['lat'][j] - data['lat_h3'][i]) ** 2 + (
                data_tochki['lon'][j] - data['lon_h3'][i]) ** 2))
    data['dist_ost'][i] = dist

data['cnt_shop'] = 0
data2 = pd.read_csv('data/osm_amenity.csv')
for i in range(len(data)):
    h3_id = data['geo_h3_10'][i]
    l = h3.k_ring(h3_id, 3)
    for j in range(len(data2)):
        h2_id = data2['geo_h3_10'][j]
        for k in l:
            t = ['Автозапчасти для иномарок', 'Авторемонт и техобслуживание (СТО)', 'Алкогольные напитки', 'Аптеки',
                 'Банки', 'Быстрое питание', 'Доставка готовых блюд', 'Женская одежда', 'Кафе',
                 'Косметика / Парфюмерия', 'Ногтевые студии', 'Овощи / Фрукты', 'Парикмахерские', 'Платёжные терминалы',
                 'Постаматы', 'Продуктовые магазины', 'Пункты выдачи интернет-заказов', 'Рестораны', 'Страхование',
                 'Супермаркеты', 'Цветы', 'Шиномонтаж']
            if h2_id == k:
                for f in range(len(t)):
                    if data2[t[f]][j] > 0:
                        data['cnt_shop'][i] += data2[t[f]][j]

for i in range(len(data)):
    data['population'][i] /= 100
    data['cnt_shop'][i] /= 100
    data['dist_inter'][i] *= 1000
    data['dist_ost'][i] *= 1000
X = data[['atm_cnt', 'dist_inter', 'population', 'dist_ost', 'cnt_shop']]
y = data['target']
data.head()


regressor = LinearRegression()
regressor.fit(X, y)
coeff_df = pd.DataFrame(regressor.coef_, X.columns, columns=['Coefficient'])
filename = 'finalized_model.sav'
pickle.dump(regressor, open(filename, 'wb'))
