from tkinter.ttk import Combobox
from tkinter import messagebox

import mysql.connector
from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
class Product:
    def __init__(self, name, category, price):
        self.name = name
        self.category = category
        self.price = price

class PurchaseRecord:
    def __init__(self, date, product):
        self.date = date
        self.product = product

class FinancialManager:
    def __init__(self):
        self.products = []
        self.purchase_records = []
        self.db_manager = db_manager
        self.load_products_from_db()

    def add_product(self, name, category, price):
        existing_product = next((p for p in self.products if p.name == name), None)

        if existing_product:
            # Если продукт уже существует в памяти, вернем его
            return existing_product

        # Создаем новый продукт и добавляем его в память
        product = Product(name, category, price)
        self.products.append(product)
        return product

    def add_purchase_record(self, date, product):
        product_id = self.db_manager.get_product_id(product)

        record = PurchaseRecord(date, product)
        self.purchase_records.append(record)

    def load_products_from_db(self):
        product_names = self.db_manager.get_all_products()
        for name in product_names:
            product = Product(name, "", 0.0)
            self.products.append(product)

    def view_all_records(self):
        return self.purchase_records


class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                category VARCHAR(255),
                price FLOAT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE,
                product_id INT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        self.conn.commit()

    def save_product(self, product):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, category, price)
            VALUES (%s, %s, %s)
        ''', (product.name, product.category, product.price))
        self.conn.commit()
        return cursor.lastrowid

    def save_purchase_record(self, date, product_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO purchase_records (date, product_id)
            VALUES (%s, %s)
        ''', (date, product_id))
        self.conn.commit()

    def get_all_records(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT purchase_records.date, products.name, products.price, products.category
            FROM purchase_records
            JOIN products ON purchase_records.product_id = products.id
        ''')
        records = cursor.fetchall()
        return records

    def get_product_id(self, product):
        cursor = self.conn.cursor()
        cursor.execute('''
               SELECT id FROM products WHERE name = %s
           ''', (product.name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_all_products(self):
        cursor = self.conn.cursor()
        cursor.execute('''
               SELECT name FROM products
           ''')
        result = cursor.fetchall()
        print("Products from database:", result)
        return [record[0] for record in result]

    def delete_record(self, date, product_name, price, category):
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM purchase_records
            WHERE date = %s AND product_id IN (
                SELECT id FROM products WHERE name = %s AND price = %s AND category = %s
            )
        ''', (date, product_name, price, category))
        self.conn.commit()

    def get_records_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT purchase_records.date, products.name, products.price, products.category
            FROM purchase_records
            JOIN products ON purchase_records.product_id = products.id
            WHERE purchase_records.date = %s
        ''', (date,))
        records = cursor.fetchall()
        return records

    def get_records_by_category(self, category):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT purchase_records.date, products.name, products.price, products.category
            FROM purchase_records
            JOIN products ON purchase_records.product_id = products.id
            WHERE products.category = %s
        ''', (category,))
        records = cursor.fetchall()
        return records

    def get_records_sorted_by_price(self, sort_order):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT purchase_records.date, products.name, products.price, products.category
            FROM purchase_records
            JOIN products ON purchase_records.product_id = products.id
            ORDER BY products.price * %s
        ''', (sort_order,))
        records = cursor.fetchall()
        return records

class GUI:
    def __init__(self, db_manager, financial_manager):
        self.db_manager = db_manager
        self.financial_manager = financial_manager

        self.root = Tk()
        self.root.title("Программа для контроля собственных денежных средств")

        self.label = Label(self.root, text="Добро пожаловать в программу!")
        self.label.pack()

        self.add_button = Button(self.root, text="Добавить продукт", command=self.add_product)
        self.add_button.pack()

        self.view_button = Button(self.root, text="Просмотреть все записи", command=self.view_records)
        self.view_button.pack()

        # Добавим Treeview для отображения записей
        self.tree = ttk.Treeview(self.root, columns=('Дата', 'Продукт', 'Цена', 'Категория'), show='headings')
        self.tree.heading('Дата', text='Дата')
        self.tree.heading('Продукт', text='Продукт')
        self.tree.heading('Цена', text='Цена')
        self.tree.heading('Категория', text='Категория')
        self.tree.pack(pady=20)

        # Выведем начальные записи
        self.view_records()

        self.purchase_button = Button(self.root, text="Записать покупку", command=self.record_purchase)
        self.purchase_button.pack()

        # Добавим кнопки для просмотра записей по дате и по категории
        view_by_date_button = Button(self.root, text="Просмотреть по дате", command=self.view_by_date)
        view_by_date_button.pack()

        view_by_category_button = Button(self.root, text="Просмотреть по категории", command=self.view_by_category)
        view_by_category_button.pack()

        # Добавим кнопку для фильтрации по цене
        self.sort_order = 1  # 1 - по возрастанию, -1 - по убыванию
        self.price_filter_button = Button(self.root, text="Фильтровать по возрастанию", command=self.filter_by_price)
        self.price_filter_button.pack()

        # Добавим кнопку удаления
        delete_button = Button(self.root, text="Удалить запись", command=self.delete_record)
        delete_button.pack()

    def record_purchase(self):
        record_purchase_window = Tk()
        record_purchase_window.title("Записать покупку")

        # Добавьте элементы управления для ввода данных о покупке
        date_label = Label(record_purchase_window, text="Дата:")
        date_label.grid(row=0, column=0)
        date_entry = DateEntry(record_purchase_window, date_pattern='yyyy-mm-dd')
        date_entry.grid(row=0, column=1)

        # Добавьте элемент управления для выбора продукта из Combobox
        product_label = Label(record_purchase_window, text="Продукт:")
        product_label.grid(row=1, column=0)

        # Получите список всех продуктов из базы данных
        all_products = self.db_manager.get_all_products()

        # Используйте Combobox для выбора продукта из списка
        product_combobox = Combobox(record_purchase_window, values=all_products)
        product_combobox.grid(row=1, column=1)

        # Функция для сохранения записи о покупке в базе данных
        def save_purchase():
            purchase_date = date_entry.get()
            product_name = product_combobox.get()

            if not product_name:
                messagebox.showwarning("Внимание", "Выберите продукт из списка.")
                return

            # Преобразуем product_name в строку, чтобы убедиться в совпадении типов
            product_name_str = str(product_name)

            # Проверим, содержится ли выбранный продукт в списке Combobox
            if product_name_str not in product_combobox['values']:
                messagebox.showwarning("Внимание", "Выбранный продукт не найден в списке.")
                return

            # Получим выбранный продукт из списка
            print("Products in financial manager:", [p.name for p in self.financial_manager.products])

            print("product_name_str:", product_name_str)
            print("Product names:", [p.name for p in self.financial_manager.products])
            selected_product = next((p for p in self.financial_manager.products if p.name == product_name_str), None)
            print("Selected product:", selected_product)

            if selected_product:
                # Получим id существующего продукта из базы данных
                product_id = self.db_manager.get_product_id(selected_product)

                # Используем существующий продукт в записи о покупке
                self.financial_manager.add_purchase_record(purchase_date, selected_product)
                self.db_manager.save_purchase_record(purchase_date, product_id)

                # Обновите список записей
                self.view_records()

                record_purchase_window.destroy()
            else:
                messagebox.showwarning("Внимание", "Выбранный продукт не найден в списке.")

        save_button = Button(record_purchase_window, text="Сохранить", command=save_purchase)
        save_button.grid(row=2, columnspan=2)

    def add_product(self):
        # Откройте окно для добавления продукта
        add_product_window = Tk()
        add_product_window.title("Добавить продукт")

        # Добавьте элементы управления для ввода данных о продукте
        name_label = Label(add_product_window, text="Название:")
        name_label.grid(row=0, column=0)
        name_entry = Entry(add_product_window)
        name_entry.grid(row=0, column=1)

        category_label = Label(add_product_window, text="Категория:")
        category_label.grid(row=1, column=0)
        category_entry = Entry(add_product_window)
        category_entry.grid(row=1, column=1)

        price_label = Label(add_product_window, text="Цена:")
        price_label.grid(row=2, column=0)
        price_entry = Entry(add_product_window)
        price_entry.grid(row=2, column=1)

        # Функция для сохранения продукта в базе данных
        def save_product():
            name = name_entry.get()
            category = category_entry.get()
            price = float(price_entry.get())
            product = self.financial_manager.add_product(name, category, price)
            self.db_manager.save_product(product)
            add_product_window.destroy()

        save_button = Button(add_product_window, text="Сохранить", command=save_product)
        save_button.grid(row=3, columnspan=2)

    def view_records(self):
        # Очистим Treeview перед обновлением
        for record in self.tree.get_children():
            self.tree.delete(record)

        # Получим все записи из базы данных
        records = self.db_manager.get_all_records()

        # Добавим записи в Treeview
        for record in records:
            self.tree.insert('', 'end', values=record)

    def delete_record(self):
        # Получим выделенную строку
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите запись для удаления.")
            return

        # Получим значения из выбранной строки
        values = self.tree.item(selected_item, 'values')
        date, product_name, price, category = values

        # Удалим запись из базы данных
        self.db_manager.delete_record(date, product_name, price, category)

        # Обновим Treeview после удаления записи
        self.view_records()

    def view_by_date(self):
        # Создадим новое окно для выбора даты
        view_window = Toplevel(self.root)
        view_window.title("Просмотр по дате")

        # Добавим элементы интерфейса для выбора даты
        date_label = Label(view_window, text="Дата:")
        date_label.grid(row=0, column=0, padx=10, pady=10)

        date_entry = DateEntry(view_window, width=12, background='darkblue', foreground='white', borderwidth=2)
        date_entry.grid(row=0, column=1, padx=10, pady=10)

        # Добавим кнопку для просмотра записей по дате
        view_button = Button(view_window, text="Просмотреть", command=lambda: self.view_records_by_date(
            date_entry.get_date(), view_window))
        view_button.grid(row=1, columnspan=2, pady=10)


    def view_by_category(self):
        # Создадим новое окно для ввода категории
        view_window = Toplevel(self.root)
        view_window.title("Просмотр по категории")

        # Добавим элементы интерфейса для ввода категории
        category_label = Label(view_window, text="Категория:")
        category_label.grid(row=0, column=0, padx=10, pady=10)
        category_entry = Entry(view_window)
        category_entry.grid(row=0, column=1, padx=10, pady=10)

        # Добавим кнопку для просмотра записей по категории
        view_button = Button(view_window, text="Просмотреть", command=lambda: self.view_records_by_category(
            category_entry.get(), view_window))
        view_button.grid(row=1, columnspan=2, pady=10)

    def view_records_by_date(self, date, view_window):
        # Очистим Treeview перед обновлением
        for record in self.tree.get_children():
            self.tree.delete(record)

        # Получим записи из базы данных по дате
        records = self.db_manager.get_records_by_date(date)

        # Добавим записи в Treeview
        for record in records:
            self.tree.insert('', 'end', values=record)

        # Закроем окно просмотра
        view_window.destroy()

    def view_records_by_category(self, category, view_window):
        # Очистим Treeview перед обновлением
        for record in self.tree.get_children():
            self.tree.delete(record)

        # Получим записи из базы данных по категории
        records = self.db_manager.get_records_by_category(category)

        # Добавим записи в Treeview
        for record in records:
            self.tree.insert('', 'end', values=record)

        # Закроем окно просмотра
        view_window.destroy()

    def filter_by_price(self):
        # Очистим Treeview перед обновлением
        for record in self.tree.get_children():
            self.tree.delete(record)

        # Получим записи из базы данных с учетом фильтрации по цене
        records = self.db_manager.get_records_sorted_by_price(self.sort_order)

        # Добавим записи в Treeview
        for record in records:
            self.tree.insert('', 'end', values=record)

        # Обновим текст кнопки в зависимости от текущего порядка сортировки
        if self.sort_order == 1:
            self.price_filter_button.config(text="Фильтровать по убыванию")
        else:
            self.price_filter_button.config(text="Фильтровать по возрастанию")

        # Изменим порядок сортировки для следующего нажатия
        self.sort_order *= -1


# Запуск программы
if __name__ == "__main__":
    db_manager = DatabaseManager(
        host="localhost",
        user="root",
        password="12345",
        database="onlineshop"
    )
    financial_manager = FinancialManager()
    gui = GUI(db_manager, financial_manager)

    gui.root.mainloop()

