import requests
from bs4 import BeautifulSoup as bs
import time
import re
from settings import CURRENCY_MAP
from currency import get_last_rate


rates = {}


def convert_currency(min_s, max_s, cur, rates 
= rates):
    min_s_c, max_s_c, rate = (min_s, max_s, 1)

    if cur.strip() and cur.strip() != 'руб' and cur.strip() != '₽':
        c_code = CURRENCY_MAP.get(cur)
        if c_code:
            if c_code in rates:
                rate = rates.get(c_code)
            else:
                rate = get_last_rate(c_code)

            if rate:
                min_s_c = min_s * rate
                max_s_c = max_s * rate
                rates[c_code] = rate
    
    return (min_s_c, max_s_c, rate)


def extract_salary(value):
    value = value.replace('—', '-')
    min, max = value.split('-') if re.search(r'\-', value) else (value, None)

    min = int(''.join(re.findall(r'(\d+)', min)))
    if min is None:
        min = 0
    max = int(''.join(re.findall(r'(\d+)', max))) if max else 0
    
    currency = ''.join(re.findall('[a-zA-Zа-яА-Я₽]+', value.replace('от ', '').replace('до ', ''))).strip()

    return min, max, currency
    

def parse_hh_vacancies(vacancies, rates = rates):
    vacancy_data = []

    for vacancy in vacancies:
        header = vacancy.find('div', class_='vacancy-serp-item__row_header')
        nl = header.find('div', class_='resume-search-item__name').find('a')
        min_s, max_s, cur = extract_salary(header.find('div', class_='vacancy-serp-item__compensation').text)
        min_s_c, max_s_c, rate = convert_currency(min_s, max_s, cur)

        vacancy_data.append({
            'title': nl.text,
            'link': nl['href'],
            'original_min_salary': min_s,
            'original_max_salary': max_s,
            'min_salary': min_s_c, 
            'max_salary': max_s_c,
            'rate': rate,
            'currency': cur,
            'source': 'hh.ru'
        })

    return vacancy_data


def parse_sj_vacancies(vacancies, rates = rates):
    vacancy_data = []

    for vacancy in vacancies:
        v = vacancy.find('div', class_='_1Tocb').nextSibling

        min_s, max_s, currency = extract_salary(v.find('span', class_='_3mfro _2Wp8I f-test-text-company-item-salary PlM3e _2JVkc _2VHxz').text)
        min_s_c, max_s_c, rate = convert_currency(min_s, max_s, currency)

        vacancy_data.append({
            'title': v.find('a').find('div').text,
            'link': v.find('a')['href'],
            'original_min_salary': min_s,
            'original_max_salary': max_s,
            'min_salary': min_s_c, 
            'max_salary': max_s_c,
            'rate': rate,
            'currency': currency, 
            'source': 'superjob.ru'
        })

    return vacancy_data


def process_link(link, source):
    print(f'Processing link: {link}...')

    data = requests.get(
        link, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
        }
    )
    
    html = bs(data.text, 'html.parser')
    
    if source == 'hh':
        vacancies = html.find_all('div', class_='vacancy-serp-item')
        vacancy_data = parse_hh_vacancies(vacancies)
        next_link = html.find('a', class_='HH-Pager-Controls-Next')['href']
    elif source == 'sj':
        vacancies = html.find_all('div', class_='_3zucV _2GPIV i6-sc _3VcZr')
        vacancy_data = parse_sj_vacancies(vacancies)
        next_link = ''
        next_link = html.find('a', class_='icMQ_ _1_Cht _3ze9n f-test-button-dalshe f-test-link-dalshe')['href']

    return (vacancy_data, next_link)


def collect_data(src):
    link = None
    final_data = []

    for s in src:
        print(f'Parsing {s["name"]}')
        link = None
        for _ in (range(4)):
            if not link:
                link = s['link']
            
            vacancy_data, next_link = process_link(link, s['name'])

            if len(vacancy_data) == 0:
                break

            final_data += vacancy_data

            if not next_link:
                break

            link = f"{s['domain']}{next_link}"
            time.sleep(6)

    return final_data