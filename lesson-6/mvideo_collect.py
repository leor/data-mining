from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import sleep

from pymongo import MongoClient

mongo = MongoClient('mongodb://127.0.0.1:27017')
db = mongo.goods

driver = webdriver.Chrome()
driver.get('https://mvideo.ru')
print(driver.title)
assert 'М.Видео' in driver.title

hits_gallery = driver.find_element_by_class_name('sel-hits-block')
paging = hits_gallery.find_elements_by_css_selector('div.carousel-paging a')

'''
Можно в приницпе опросить АПИ:
https://www.mvideo.ru/browse/product/gallery-product-list.jsp?galleryId=block5260655&pageType=application&prodId=Site_1&startFrom=5&ref=true&requestId=
но там возращается готовый HTML и проку от этого немного
'''
for i, page in enumerate(paging):
    print(f'current {page.text}')
    if 'selected' in page.get_attribute('class'):
        print('pass...')
        continue

    print(f'clicking {page.text}')
    page.click()

    selector = '.sel-hits-block li[rel="%d"]' % (i*4 + 3)

    print(f'waiting for {selector}')
    new_item = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    print(new_item.get_attribute('rel'))

    print('done')

entities = hits_gallery.find_elements_by_tag_name('li')

for entity in entities:
    item = {}
    # вообще, в этом элементе есть аттрибут data-product-info, где есть часть информации, но это не наш метод :)
    item['link'] = entity.find_element_by_tag_name('a').get_attribute('href')
    item['image'] = entity.find_element_by_css_selector('img.product-tile-picture__image').get_attribute('data-original')
    item['title'] = entity.find_element_by_css_selector('div.c-product-tile__description h4').text
    item['price'] = entity.find_element_by_class_name('c-pdp-price__current').text

    print(item)
    
    db.goods.update_one(
        {'link': item['link']},
        {'$set': item},
        upsert=True
    )

driver.quit()

print(f"Записей в БД {db.goods.count_documents({})}")