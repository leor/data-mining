from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from pymongo import MongoClient

mongo = MongoClient('mongodb://127.0.0.1:27017')
db = mongo.emails

driver = webdriver.Chrome()
driver.get('https://yandex.ru')
assert 'Яндекс' in driver.title

driver.find_element_by_class_name('desk-notif-card__login-enter-expanded').click()
assert 'Авторизация' in driver.title

login = driver.find_element_by_id('passp-field-login')
login.send_keys('mikhail.levanov@yandex.ru')
login.submit()

password = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'passp-field-passwd'))
)
# нужен пароль
password.send_keys('')
password.submit()

msg_list = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'mail-MessagesList'))
)
email_list = driver.find_elements_by_css_selector('.mail-MessageSnippet-Wrap a')
i = 0

links = []

for email_link in email_list:
    links.append(email_link.get_attribute('href'))

for link in links:
    print(f'Обработка {link}')
    driver.get(link)

    heads = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'js-message-heads'))
    )

    item = {}
    item['link'] = link

    subject = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'mail-Message-Toolbar-Subject'))
    )
    item['subject'] = subject.text

    date = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'mail-Message-Date'))
    )
    item['date'] = date.text

    sender = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'mail-Message-Sender-Name'))
    )
    item['sender'] = sender.text

    sender_email = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'mail-Message-Sender-Email'))
    )
    item['sender_email'] = sender_email.text

    body_content = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'mail-Message-Body-Content'))
    )
    item['text'] = body_content.get_attribute('innerHTML')
    
    db.emails.update_one(
        {'link': item['link']},
        {'$set': item},
        upsert=True
    )

    driver.back()
    msg_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'mail-MessagesList'))
    )

driver.quit()

print(f'Всего собрано {db.emails.count_documents({})} писем')
