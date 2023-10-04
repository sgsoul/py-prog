from HW.product import Product


class Purchase:
    def __init__(self, product_id, date):
        self.product_id = product_id
        self.date = date

    def get_date(self):
        return self.date

