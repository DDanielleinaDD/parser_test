import requests
from lxml import html

from create_bd import create_bd_user, add_userinfo, add_wishlist_without_review, add_wishlist_with_review


URL_FOR_PARSING={'URL_LOGIN': 'https://siriust.ru/',
                 'URL_PROFILE': 'https://siriust.ru/profiles-update/',
                 'URL_WISHLIST': 'https://siriust.ru/wishlist/'}

user_xpath = {
    'email': '//input[@name="user_data[email]"]/@value',
    'first_name': '//input[@name="user_data[s_firstname]"]/@value',
    'last_name': '//input[@name="user_data[s_lastname]"]/@value',
    'city': '//input[@name="user_data[s_city]"]/@value',
}

wishlist_xpath = {
    'href': '//a[@class="abt-single-image"]/@href',
    'name': '//a[@class="product-title"]/@title',
    'price': '//span[@class="ty-price-num"]/text()',
    'available_shop': '//div[@class="ty-product-feature"]',
    'count_review': '//a[@class="ty-discussion__review-a cm-external-click"]/text()',
    'star_full': '//div[@class="ty-discussion__rating-wrapper"]//i[@class="ty-stars__icon ty-icon-star"]',
    'star_half': '//div[@class="ty-discussion__rating-wrapper"]//i[@class="ty-stars__icon ty-icon-star-half"]',
    'reviews': '//div[@class="ty-discussion-post__content ty-mb-l"]//div[@class="ty-discussion-post__message"]/text()[1]',
    'button_pagination': '//div[@class="ty-pagination"]//a[@class="ty-pagination__item ty-pagination__btn ty-pagination__next cm-history cm-ajax ty-pagination__right-arrow"]/@href'
}

class Parse_Siruist():
    '''Класс для парсинга сайта.'''
    def __init__(self):
        self.session = requests.Session()
        self.headers_for_page = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/112.0'}

    # Авторизуемся на сайте, если успешно, то создаем БД
    def login(self, login_data):
        response = self.session.post(URL_FOR_PARSING['URL_LOGIN'], headers=self.headers_for_page, data=login_data)
        if 'Вы успешно авторизовались' in response.text:
            print("Аутентификация прошла успешно!")
            create_bd_user()
            return True
        else:
            raise Exception("Ошибка входа!")


    # Получаем Имя, Фамилию, город, почту пользователя
    def get_profile(self):
        profile = self.session.get(URL_FOR_PARSING['URL_PROFILE'], headers=self.headers_for_page)
        profile_html = html.fromstring(profile.content)
        email = profile_html.xpath(user_xpath['email'])
        first_name = profile_html.xpath(user_xpath['first_name'])
        last_name = profile_html.xpath(user_xpath['last_name'])
        city = profile_html.xpath(user_xpath['city'])
        user_info = [*email, *first_name, *last_name, *city]
        add_userinfo(user_info)
        print(' - '.join(user_info))


    # Получаем отзывы по продуктам
    def get_review_from_next_page(self, html_page, review_list=None):
        if review_list is None:
            review_list = []
        next_page_review = html_page.xpath(wishlist_xpath['button_pagination'])
        page_next = self.session.get(next_page_review[0], headers=self.headers_for_page)
        html_page_next = html.fromstring(page_next.content)
        reviews = html_page_next.xpath(wishlist_xpath['reviews'])
        review_list.append(reviews)
        if len(html_page_next.find_class(wishlist_xpath['button_pagination'])) > 0:
            self.get_review_from_next_page(self.session, html_page_next, review_list)
        return review_list


    # Получаем информацию о товарах в избранном
    def wishlist(self):
        favorite_items = self.session.get(URL_FOR_PARSING['URL_WISHLIST'], headers=self.headers_for_page)
        favorites_html = html.fromstring(favorite_items.content)
        href = favorites_html.xpath(wishlist_xpath['href'])
        name = favorites_html.xpath(wishlist_xpath['name'])
        for href_1, name_1 in zip(href, name):
            favorite_item = self.session.get(href_1, headers=self.headers_for_page)
            html_page = html.fromstring(favorite_item.content)
            price = html_page.xpath(wishlist_xpath['price'])[0]
            available_shop = len(html_page.xpath(wishlist_xpath['available_shop'])) - 1
            count_review = html_page.xpath(wishlist_xpath['count_review'])
            star_full = len(html_page.xpath(wishlist_xpath['star_full']))
            star_half = len(html_page.xpath(wishlist_xpath['star_half']))
            if star_half > 0:
                star_full = star_full + 0.5

            if len(count_review) > 0:
                reviews = html_page.xpath(wishlist_xpath['reviews'])
                if len(html_page.find_class(wishlist_xpath['button_pagination'])) > 0:
                    another_rev = self.get_review_from_next_page(html_page=html_page)
                    for review in another_rev[0]:
                        reviews.append(review)
                wishlist = [name_1, price, star_full, *count_review, available_shop]
                add_wishlist_with_review(wishlist, name_1, reviews)
            else:
                reviews = 'Нет отзывов'
                count_review =['0 отзывов']
                wishlist = [name_1, price, star_full, *count_review, available_shop]
                add_wishlist_without_review(wishlist)

            print(f'Товар: {name_1}, '
                f'Цена товара: {price}, '
                f'Доступные магазины: {available_shop}, '
                f'Количество отзывов: {count_review[0]}, '
                f'Оценка: {star_full}, '
                f'Отзывы: {reviews}')


        # Основная логика программы
    def main(self):
        login_data = {
                'user_login': input('Введите ваш email:'),
                'password': input('Введите ваш пароль:'),
                'dispatch[auth.login]': ''
            }
        if self.login(login_data):
            self.get_profile()
            self.wishlist()


if __name__ == '__main__':
    parser = Parse_Siruist()
    parser.main()
