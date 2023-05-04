import requests
from lxml import html
import sqlite3


URL_LOGIN = 'https://siriust.ru/'
URL_PROFILE = 'https://siriust.ru/profiles-update/'
URL_WISHLIST = 'https://siriust.ru/wishlist/'

headers_for_page = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/112.0'}


# Создаем базу данных и таблицы для сохранения информации
def create_bd_user():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT NOT NULL,
                   first_name TEXT,
                   last_name TEXT,
                   city TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS wishlist
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   price FLOAT NOT NULL,
                   rating FLOAT NULL,
                   count_review TEXT NULL,
                   availablity INTEGER NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   review TEXT,
                   product_id INTEGER,
                   FOREIGN KEY (product_id) REFERENCES wishlist(id))''')
    conn.commit()
    conn.close()


# Авторизуемся на сайте, если успешно, то создаем БД
def login(session, login_data):
    response = session.post(URL_LOGIN, headers=headers_for_page, data=login_data)
    if 'Вы успешно авторизовались' in response.text:
        print("Аутентификация прошла успешно!")
        create_bd_user()
        return True
    else:
        print("Ошибка входа!")
        return False

# Получаем Имя, Фамилию, город, почту пользователя
def get_profile(session):
    profile = session.get(URL_PROFILE, headers=headers_for_page)
    profile_html = html.fromstring(profile.content)
    email = profile_html.xpath('//input[@name="user_data[email]"]/@value')
    first_name = profile_html.xpath('//input[@name="user_data[s_firstname]"]/@value')
    last_name = profile_html.xpath('//input[@name="user_data[s_lastname]"]/@value')
    city = profile_html.xpath('//input[@name="user_data[s_city]"]/@value')
    user_info = [*email, *first_name, *last_name, *city]
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user (email, first_name, last_name, city) VALUES (?, ?, ?, ?)",
                   user_info)
    conn.commit()
    conn.close()      
    print(' - '.join(user_info))


# Получаем отзывы по продуктам
def get_review_from_next_page(session, html_page, review_list=None):
    if review_list is None:
        review_list = []
    next_page_review = html_page.xpath('//div[@class="ty-pagination"]//a[@class="ty-pagination__item ty-pagination__btn ty-pagination__next cm-history cm-ajax ty-pagination__right-arrow"]/@href')
    page_next = session.get(next_page_review[0], headers=headers_for_page)
    html_page_next = html.fromstring(page_next.content)
    reviews = html_page_next.xpath('//div[@class="ty-discussion-post__content ty-mb-l"]//div[@class="ty-discussion-post__message"]/text()[1]')
    review_list.append(reviews)
    if len(html_page_next.find_class("ty-pagination__item ty-pagination__btn ty-pagination__next cm-history cm-ajax ty-pagination__right-arrow")) > 0:
        get_review_from_next_page(session, html_page_next, review_list)
    return review_list


# Получаем информацию о товарах в избранном
def wishlist(session):
    favorite_items = session.get(URL_WISHLIST, headers=headers_for_page)
    favorites_html = html.fromstring(favorite_items.content)
    href = favorites_html.xpath('//a[@class="abt-single-image"]/@href')
    name = favorites_html.xpath('//a[@class="product-title"]/@title')
    for href_1, name_1 in zip(href, name):
        favorite_item = session.get(href_1, headers=headers_for_page)
        html_page = html.fromstring(favorite_item.content)
        price = html_page.xpath('//span[@class="ty-price-num"]/text()')[0]
        available_shop = len(html_page.xpath('//div[@class="ty-product-feature"]')) - 1
        count_review = (html_page.xpath('//a[@class="ty-discussion__review-a cm-external-click"]/text()'))
        star_full = len(html_page.xpath('//div[@class="ty-discussion__rating-wrapper"]//i[@class="ty-stars__icon ty-icon-star"]'))
        star_half = len(html_page.xpath('//div[@class="ty-discussion__rating-wrapper"]//i[@class="ty-stars__icon ty-icon-star-half"]'))
        if star_half > 0:
            star_full = star_full + 0.5
        if len(count_review) > 0:
            reviews = html_page.xpath('//div[@class="ty-discussion-post__content ty-mb-l"]//div[@class="ty-discussion-post__message"]/text()[1]')
            if len(html_page.find_class("ty-pagination__item ty-pagination__btn ty-pagination__next cm-history cm-ajax ty-pagination__right-arrow")) > 0:
                another_rev = get_review_from_next_page(session, html_page)
                for review in another_rev[0]:
                    reviews.append(review)
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO wishlist (name, price, rating, count_review, availablity) VALUES (?, ?, ?, ?, ?)",
                           (name_1, price, star_full, *count_review, available_shop))
            cursor.execute('SELECT id FROM wishlist WHERE name = ?', (name_1,))
            result = cursor.fetchone()
            product_id = result[0]
            for review in reviews:
                cursor.execute(f'INSERT INTO reviews (review, product_id) VALUES (?, ?)', (review, product_id))
            conn.commit()
            conn.close()
        else:
            reviews = 'Нет отзывов'
            count_review =['0 отзывов']
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO wishlist (name, price, rating, count_review, availablity) VALUES (?, ?, ?, ?, ?)",
                           (name_1, price, star_full, *count_review, available_shop))
            conn.commit()
            conn.close()
        print(f'Товар: {name_1}, '
              f'Цена товара: {price}, '
              f'Доступные магазины: {available_shop}, '
              f'Количество отзывов: {count_review[0]}, '
              f'Оценка: {star_full}, '
              f'Отзывы: {reviews}')


# Основная логика программы
def main():
    session = requests.Session()
    login_data = {
        'user_login': input('Введите ваш email:'),
        'password': input('Введите ваш пароль:'),
        'dispatch[auth.login]': ''
    }
    if login(session, login_data):
        get_profile(session)
        wishlist(session)


if __name__ == '__main__':
    main()
