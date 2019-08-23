from zeep import Client
from zeep.helpers import serialize_object
from pymongo import MongoClient
from datetime import datetime, timedelta

client = Client('https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL')

mongo = MongoClient('mongodb://127.0.0.1:27017')
database = mongo.vacancies

# получаем список всех валют
def get_currencies(c = client):
    currencies = c.service.EnumValutes(False)
    result = [v['EnumValutes'] for v in serialize_object(currencies._value_1._value_1, target_cls=dict)]
    return result


def show_currencies(c = client):
    currencies = get_currencies(c)
    
    for c in currencies:
        print(f'{c["Vcode"]} ({c["VcharCode"].strip()}): {c["Vname"].strip()}')


def get_last_rate(code, c=client):
    today = datetime.now().strftime('%Y-%m-%d')
    r = get_rates(today, today, code, c)

    return r[0]['Vcurs']


def get_rates(from_date, to_date, code, c=client):
    rates = c.service.GetCursDynamic(from_date, to_date, code)
    result = []

    # в приницпе, можно было и через map сделать
    for r in serialize_object(rates._value_1._value_1, target_cls=dict):
        tmp = r['ValuteCursDynamic']
        tmp['Vnom'] = float(tmp['Vnom'])
        tmp['Vcurs'] = float(tmp['Vcurs'])

        result.append(tmp)

    return result


def save_rates(data, db = database):
    for rate in data:
        db.currency_rates.update_one(
            {'Vcode': rate['Vcode'], 'CursDate': rate['CursDate']},
            {'$set': rate},
            upsert = True
        )

def load_rates(from_date, to_date, code, db = database):
    rates = db.currency_rates.find({
        'Vcode': code,
        'CursDate': {
            '$gt': datetime.strptime(from_date, '%Y-%m-%d') - timedelta(days=1),
            '$lte': datetime.strptime(to_date, '%Y-%m-%d')
        }
    })

    return [r for r in rates]


def find_best(from_date, to_date, code, refresh=False, c = client, db=database):
    currencies = get_currencies(c)
    currency = next(cur for cur in currencies if cur['Vcode'].strip() == code)

    if refresh:
        r = get_rates(from_date, to_date, code, c)
        save_rates(r)

    # вариант с БД
    res = load_rates(from_date, to_date, code, db)
    max_rate = max(res, key=lambda x: x['Vcurs'])
    min_rate = min(res, key=lambda x: x['Vcurs'])

    print(f'Валюту {currency["VcharCode"]} выгодно было купить {min_rate["CursDate"].strftime("%d.%m.%Y")}, а продать {max_rate["CursDate"].strftime("%d.%m.%Y")}. Прибыль: {round(max_rate["Vcurs"] - min_rate["Vcurs"], 4)}')


if __name__ == '__main__':
    # выводим все доступные валюты
    # show_currencies()

    # R01235 - это USD
    
    # курс на сегодня
    # print(get_last_rate('R01235'))

    # запрашиваем сервис
    # r = get_rates('2019-08-20', '2019-08-23', 'R01235')
    
    # print(f'Получено {len(r)} записей')
    # сохраняем в БД
    # save_rates(r)

    # ищем данные за указанный период
    # l = load_rates('2019-08-20', '2019-08-23', 'R01235')
    # print(f'Загружено из БД {len(l)} записей')
    
    # ищем лучшие
    # ключ Refresh вызовет запрос к сервису и сохранение данных в БД
    find_best('2019-08-15', '2019-08-23', 'R01235', refresh=True)
    # а тут уже без запросы к сервису
    find_best('2019-08-20', '2019-08-22', 'R01235')
