import sqlite3

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

def add_userinfo(user_info):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user (email, first_name, last_name, city) VALUES (?, ?, ?, ?)",
                   user_info)
    conn.commit()
    conn.close()

def add_wishlist_without_review(wishlist):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO wishlist (name, price, rating, count_review, availablity) VALUES (?, ?, ?, ?, ?)",
                        wishlist)
        conn.commit()
        conn.close()

def add_wishlist_with_review(wishlist, name_1, reviews):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO wishlist (name, price, rating, count_review, availablity) VALUES (?, ?, ?, ?, ?)",
                        wishlist)
        cursor.execute('SELECT id FROM wishlist WHERE name = ?', (name_1,))
        result = cursor.fetchone()
        product_id = result[0]
        for review in reviews:
            cursor.execute(f'INSERT INTO reviews (review, product_id) VALUES (?, ?)', (review, product_id))
        conn.commit()
        conn.close()