from MySQLManager import MySQLManager
from HW.GUI import GUI


if __name__ == "__main__":
    host = "localhost"
    user = "sgsoul"
    password = "qwerty"
    database = "money_mngt"

    mysql_manager = MySQLManager(host, user, password, database)
    gui = GUI(mysql_manager)
    gui.run()

    mysql_manager.close()
