from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox

from HW.product import Product
from HW.purchase import Purchase


class GUI:
    def __init__(self, mysql_manager):
        self.mysql_manager = mysql_manager
        self.window = Tk()
        self.window.title("Программа для контроля собственных денежных средств")
        self.sort_order = "asc"

        self.product_label = Label(self.window, text="Продукт:")
        self.product_label.grid(row=0, column=0)

        self.product_combobox = ttk.Combobox(self.window, values=self.mysql_manager.get_products())
        self.product_combobox.grid(row=0, column=1)

        self.date_label = Label(self.window, text="Дата:")
        self.date_label.grid(row=1, column=0)

        self.date_var = StringVar()
        self.date_entry = Entry(self.window, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=1)

        self.add_purchase_button = Button(self.window, text="Добавить покупку", command=self.add_purchase)
        self.add_purchase_button.grid(row=2, column=0, columnspan=2)

        self.product_name_label = Label(self.window, text="Имя продукта:")
        self.product_name_label.grid(row=3, column=0)

        self.product_name_entry = Entry(self.window)
        self.product_name_entry.grid(row=3, column=1)

        self.category_label = Label(self.window, text="Категория:")
        self.category_label.grid(row=4, column=0)

        self.category_entry = Entry(self.window)
        self.category_entry.grid(row=4, column=1)

        self.price_label = Label(self.window, text="Цена:")
        self.price_label.grid(row=5, column=0)

        self.price_entry = Entry(self.window)
        self.price_entry.grid(row=5, column=1)

        self.add_product_button = Button(self.window, text="Добавить продукт", command=self.add_product)
        self.add_product_button.grid(row=6, column=0, columnspan=2)

        # Добавляем элементы для ввода даты и категории
        self.date_label = Label(self.window, text="Дата:")
        self.date_label.grid(row=8, column=0)

        self.date_entry = Entry(self.window)
        self.date_entry.grid(row=8, column=1)

        self.category_label = Label(self.window, text="Категория:")
        self.category_label.grid(row=9, column=0)

        # Создайте и заполните комбобокс категорий
        self.categories = self.mysql_manager.get_categories()
        self.category_var = StringVar(value=self.categories[0] if self.categories else "")
        self.category_combobox = ttk.Combobox(self.window, textvariable=self.category_var, values=self.categories)
        self.category_combobox.grid(row=9, column=1)

        # Добавляем кнопки и привязываем к ним функции
        self.view_by_date_button = Button(self.window, text="Просмотр по дате", command=self.view_by_date)
        self.view_by_date_button.grid(row=10, column=0, columnspan=2)

        self.view_by_category_button = Button(self.window, text="Просмотр по категории", command=self.view_by_category)
        self.view_by_category_button.grid(row=11, column=0, columnspan=2)

        self.sort_by_price_button = Button(self.window, text="Сортировать по возрастанию", command=self.sort_by_price)
        self.sort_by_price_button.grid(row=12, column=0, columnspan=2)

        self.delete_button = Button(self.window, text="Удалить запись", command=self.delete_purchase)
        self.delete_button.grid(row=13, column=0, columnspan=2)

        self.purchases_tree = ttk.Treeview(self.window, columns=("Purchase ID", "Product ID", "Name", "Category",
                                                                 "Price", "Date"))
        self.purchases_tree.heading("#1", text="Purchase ID")
        self.purchases_tree.heading("#2", text="Product ID")
        self.purchases_tree.heading("#3", text="Name")
        self.purchases_tree.heading("#4", text="Category")
        self.purchases_tree.heading("#5", text="Price")
        self.purchases_tree.heading("#6", text="Date")
        self.purchases_tree.grid(row=7, column=0, columnspan=2)

    def add_purchase(self):
        selected_product = self.product_combobox.get()
        date = self.date_var.get()

        if selected_product and date:
            try:
                date = datetime.strptime(date, '%Y-%m-%d')  # Парсим строку даты
                product = Product(selected_product, "", 0)  # Создаем объект Product с выбранным именем
                product_id = self.get_product_id_by_name(selected_product)  # Получаем product_id
                if product_id is not None:
                    purchase = Purchase(product_id, date)  # Создаем объект Purchase
                    self.mysql_manager.add_purchase(purchase)  # Передаем объект Purchase
                    self.date_entry.delete(0, END)
                    self.load_purchases()
                else:
                    messagebox.showerror("Ошибка", "Продукт не найден")
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректный формат даты")
        else:
            messagebox.showerror("Ошибка", "Выберите продукт и введите дату для добавления записи о покупке")

    def add_product(self):
        name = self.product_name_entry.get()
        category = self.category_var.get()
        price = self.price_entry.get()
        if name and category and price:
            product = Product(name, category, price)  # Создаем объект Product
            self.mysql_manager.add_product(product)  # Передаем объект Product
            self.product_name_entry.delete(0, END)
            self.category_entry.delete(0, END)
            self.price_entry.delete(0, END)
            self.load_products()
        else:
            messagebox.showerror("Ошибка", "Заполните все поля для добавления продукта")

    def get_product_id_by_name(self, product_name):
        # Получение ID продукта по его имени из базы данных
        select_product_id = "SELECT id FROM products WHERE name = %s"
        self.mysql_manager.cursor.execute(select_product_id, (product_name,))
        result = self.mysql_manager.cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def load_purchases(self):
        # Загрузка записей о покупках из базы данных и отображение их в дереве
        self.purchases_tree.delete(*self.purchases_tree.get_children())
        select_purchases = ("SELECT purchases.id, products.id, products.name, products.category, products.price, "
                            "purchases.date FROM purchases JOIN products ON purchases.product_id = products.id")
        self.mysql_manager.cursor.execute(select_purchases)
        purchases = self.mysql_manager.cursor.fetchall()
        for purchase in purchases:
            self.purchases_tree.insert("", "end", values=purchase)

    def display_purchases(self, purchases=None):
        # Очищаем дерево с записями о покупках
        for item in self.purchases_tree.get_children():
            self.purchases_tree.delete(item)

        if purchases is None:
            # Если purchases не передан, получаем все записи о покупках
            purchases = self.mysql_manager.get_all_purchases()

        # Отображаем записи о покупках в дереве
        for purchase in purchases:
            self.purchases_tree.insert("", "end", values=purchase)

    def load_products(self):
        # Загрузка продуктов из базы данных и обновление выпадающего списка
        products = self.mysql_manager.get_products()
        self.product_combobox["values"] = products

    def view_by_date(self):
        date = self.date_entry.get()
        if date:
            purchases = self.mysql_manager.get_purchases_by_date(date)
            self.display_purchases(purchases)
        else:
            messagebox.showerror("Ошибка", "Введите дату для просмотра записей")

    def view_by_category(self):
        category = self.category_var.get()  # Получаем выбранную категорию
        if category:
            purchases = self.mysql_manager.get_purchases_by_category(category)
            self.display_purchases(purchases)
        else:
            messagebox.showerror("Ошибка", "Выберите категорию для просмотра записей")

    def sort_by_price(self):
        if self.sort_order == "asc":
            purchases = self.mysql_manager.sort_purchases_by_price(ascending=True)
            self.sort_order = "desc"
            self.sort_by_price_button.config(text="Сортировать по убыванию")
        else:
            purchases = self.mysql_manager.sort_purchases_by_price(ascending=False)
            self.sort_order = "asc"
            self.sort_by_price_button.config(text="Сортировать по возрастанию")

        self.display_purchases(purchases)

    def delete_purchase(self):
        selected_item = self.purchases_tree.selection()
        if selected_item:
            purchase_id = self.purchases_tree.item(self.purchases_tree.selection()[0])["values"][0]
            self.mysql_manager.delete_purchase(purchase_id)
            self.load_purchases()
        else:
            messagebox.showerror("Ошибка", "Выберите запись для удаления")

    def run(self):
        self.load_products()  # Загрузка списка продуктов при запуске приложения
        self.load_purchases()  # Загрузка записей о покупках при запуске приложения
        self.window.mainloop()