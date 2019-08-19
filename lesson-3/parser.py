import requests
from bs4 import BeautifulSoup as bs
from pprint import pprint


def parse_vacancies(vacancies):
    vacancy_data = []

    for vacancy in vacancies:
        header = vacancy.find('div', class_='vacancy-serp-item__row_header')
        nl = header.find('div', class_='resume-search-item__name').find('a')
        salary = header.find('div', class_='vacancy-serp-item__compensation')
        vacancy_data.append({
            'title': nl.text,
            'link': nl['href'],
            'salary': salary.text
        })

    return vacancy_data


def process_link(link):
    print(f'Processing link: {link}...')

    data = requests.get(
        link, 
        headers={
            'User-Agent': 'PostmanRuntime/7.15.2'
        }
    )

    html = bs(data.text, 'html.parser')
    vacancies = html.find_all('div', class_='vacancy-serp-item')

    vacancy_data = parse_vacancies(vacancies)

    next_link = html.find('a', class_='HH-Pager-Controls-Next')['href']

    return (vacancy_data, next_link)


if __name__ == '__main__':
    lang = input('Введите желаемый язык программирования (Java, Ruby, Python, PHP etc.): ')

    # hh.ru
    link = None
    final_data = []

    for i in (range(4)):
        if not link:
            link = f'https://hh.ru/search/vacancy?only_with_salary=true&clusters=true&search_field=name&enable_snippets=true&salary=&text=Разработчик+{lang}'
        
        vacancy_data, next_link = process_link(link)

        if len(vacancy_data) == 0:
            break

        final_data += vacancy_data

        if not next_link:
            break

        link = f'https://hh.ru{next_link}'

    print('Total vacancies found: ', len(final_data))
    pprint(final_data)