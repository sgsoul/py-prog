import mysql.connector


class MySQLManager:
    def __init__(self, host, user, password, database):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        # Создание таблиц в базе данных, если они еще не существуют
        create_products_table = """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(255) NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
        """
        create_purchases_table = """
        CREATE TABLE IF NOT EXISTS purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            date DATE NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """
        self.cursor.execute(create_products_table)
        self.cursor.execute(create_purchases_table)
        self.connection.commit()

    def add_product(self, product):
        # Добавление продукта в базу данных
        insert_product = """
        INSERT INTO products (name, category, price)
        VALUES (%s, %s, %s)
        """
        self.cursor.execute(insert_product, (product.name, product.category, product.price))
        self.connection.commit()

    def add_purchase(self, purchase):
        # Добавление записи о покупке в базу данных
        insert_purchase = """
        INSERT INTO purchases (product_id, date)
        VALUES (%s, %s)
        """
        self.cursor.execute(insert_purchase, (purchase.product_id, purchase.date))
        self.connection.commit()

    def get_products(self):
        # Получение списка продуктов из базы данных
        select_products = "SELECT name FROM products"
        self.cursor.execute(select_products)
        return self.cursor.fetchall()

    def get_product_info(self, product_id):
        # Получение информации о продукте по его ID
        select_product_info = "SELECT name, category, price FROM products WHERE id = %s"
        self.cursor.execute(select_product_info, (product_id,))
        return self.cursor.fetchone()

    def get_all_purchases(self):
        # Получение всех записей о покупках из базы данных
        select_all_purchases = """
        SELECT purchases.id, products.id, products.name, products.category, products.price, purchases.date
        FROM purchases
        JOIN products ON purchases.product_id = products.id
        """
        self.cursor.execute(select_all_purchases)
        return self.cursor.fetchall()

    def get_purchases_by_date(self, date):
        # Получение записей о покупках по заданной дате
        select_purchases_by_date = """
        SELECT purchases.id, products.id, products.name, products.category, products.price, purchases.date
        FROM purchases
        JOIN products ON purchases.product_id = products.id
        WHERE purchases.date = %s
        """
        self.cursor.execute(select_purchases_by_date, (date,))
        return self.cursor.fetchall()

    def get_purchases_by_category(self, category):
        # Получение записей о покупках по заданной категории
        select_purchases_by_category = """
        SELECT purchases.id, products.id, products.name, products.category, products.price, purchases.date
        FROM purchases
        JOIN products ON purchases.product_id = products.id
        WHERE products.category = %s
        """
        self.cursor.execute(select_purchases_by_category, (category,))
        return self.cursor.fetchall()

    def sort_purchases_by_price(self, ascending=True):
        # Сортировка записей о покупках по цене (возрастающая или убывающая)
        order = "ASC" if ascending else "DESC"
        select_purchases_by_price = """
        SELECT purchases.id, products.id, products.name, products.category, products.price, purchases.date
        FROM purchases
        JOIN products ON purchases.product_id = products.id
        ORDER BY products.price {}
        """.format(order)
        self.cursor.execute(select_purchases_by_price)
        return self.cursor.fetchall()

    def delete_purchase(self, purchase_id):
        # Удаление записи о покупке из базы данных
        delete_purchase_query = "DELETE FROM purchases WHERE id = %s"
        self.cursor.execute(delete_purchase_query, (purchase_id,))
        self.connection.commit()

    def get_categories(self):
        # Получение уникальных категорий из базы данных
        select_categories = "SELECT DISTINCT category FROM products"
        self.cursor.execute(select_categories)
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        self.cursor.close()
        self.connection.close()