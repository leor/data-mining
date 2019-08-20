'''
Этот скрипт парсит данные с сайтов и собирает их в MongoDB
'''

from parser import collect_data
from pymongo import MongoClient
from contextlib import closing
from settings import MONGO_SETTINGS


SRC = [
    {
        'link': 'https://hh.ru/search/vacancy?only_with_salary=true&clusters=true&search_field=name&enable_snippets=true&salary=&text=Разработчик', 
        'domain': 'https://hh.ru',
        'name': 'hh'
    },
    {
        'link': 'https://www.superjob.ru/vakansii/programmist.html?payment_defined=1&geo%5Bc%5D%5B0%5D=1', 
        'domain': 'https://www.superjob.ru',
        'name': 'sj'
    }
]


def save_data(data):
    with closing(MongoClient(f'mongodb://{MONGO_SETTINGS["host"]}:{MONGO_SETTINGS["port"]}')) as client:
        db = client.vacancies

        '''
        Так мы сохраняем новые и обновляем старые даннные, опираясь на ссылку
        Не стал заморачиваться с Уникальным ключом
        Можно сделать update_many, но нужен критерий выборки, а я что-то с ним не очень разобрался
        '''
        for item in data:
            db.vacancies.update_one(
                {'link': item['link']},
                {'$set': item},
                upsert=True
            )
    


if __name__ == '__main__':
    data = collect_data(SRC)
    
    print('Total vacancies found: ', len(data))
    print(data)

    save_data(data)

    print('DB updated')