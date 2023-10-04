class Product:
    def __init__(self, name, category, price):
        self.name = name
        self.category = category
        self.price = price

    def get_name(self):
        return self.name

    def get_category(self):
        return self.category

    def get_price(self):
        return self.price
