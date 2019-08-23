from pymongo import MongoClient
from contextlib import closing
from settings import MONGO_SETTINGS
from argparse import ArgumentParser
from pandas import DataFrame
import pymongo


arg_parser = ArgumentParser()

arg_parser.add_argument(
    '-min', '--min_salary', type=int, required=False,
    help='Minimum salary'
)

args = arg_parser.parse_args()


if __name__ == '__main__':
    min = args.min_salary if args.min_salary else 0

    result = []
    with closing(MongoClient(f'mongodb://{MONGO_SETTINGS["host"]}:{MONGO_SETTINGS["port"]}')) as client:
        db = client.vacancies

        for row in db.vacancies.find({'min_salary': {'$gt': min}}).sort('min_salary', pymongo.ASCENDING):
            result.append(row)

    df = DataFrame(result, columns=['title', 'link', 'min_salary', 'max_salary', 'original_min_salary', 'original_max_salary', 'rate', 'currency', 'source'])
    
    print(df)