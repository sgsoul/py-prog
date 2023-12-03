from abc import ABC, abstractmethod
import abc
import time
from functools import wraps
def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"Вызов {func.__name__}...")
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} завершен за {end_time - start_time:.2f} секунд")
        return result
    return wrapper
def check_conditions(func):
    @wraps(func)
    def wrapper(self, x, y, *args, **kwargs):
        if 0 <= x <= 7 and 0 <= y <= 7:
            result = func(self, x, y, *args, **kwargs)
            if 0 <= self.x <= 7 and 0 <= self.y <= 7:
                return result
            else:
                print("Постусловие не выполнено: фигура за пределами поля")
                self.x, self.y = x, y
        else:
            print("Предусловие не выполнено: целевая позиция за пределами поля")
    return wrapper
def capitalize_output(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        original_output = func(*args, **kwargs)
        return original_output.upper() if isinstance(original_output, str) else original_output
    return wrapper
class ABCMetaWithRegistry(abc.ABCMeta):
    _registry = []
class ChessMeta(ABCMetaWithRegistry):
    def __new__(cls, name, bases, class_dict):
        new_class = super().__new__(cls, name, bases, class_dict)
        cls._registry.append(new_class)
        return new_class
class ChessPiece(metaclass=ChessMeta):
    def __init__(self, x, y, color):
        self._x = x
        self._y = y
        self._color = color
    @abstractmethod
    def move(self, x, y):
        pass
    def draw(self):
        print(f"{self.__class__.__name__} на ({self.x}, {self.y}), цвет: {self.color}")
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        self._x = value
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        self._y = value
    @property
    def color(self):
        return self._color
class CanCapture:
    def capture(self, other):
        if isinstance(other, ChessPiece) and other.color != self.color:
            print(f"{self.__class__.__name__} победил {other.__class__.__name__}")
            return True
        print(f"{self.__class__.__name__} не может победить {other.__class__.__name__}")
        return False
class Figure(ChessPiece):
    def __add__(self, other):
        if isinstance(other, ChessPiece):
            return Figure(self.x + other.x, self.y + other.y, self.color)
        return NotImplemented
    def __sub__(self, other):
        if isinstance(other, ChessPiece):
            return Figure(self.x - other.x, self.y - other.y, self.color)
        return NotImplemented
class Pawn(Figure, CanCapture):
    def __init__(self, x=0, y=0, color='белый'):
        super().__init__(x, y, color)
        self._first_move = True
    def move(self, x, y):
        dx = x - self.x
        dy = y - self.y
        if self.color == 'белый' and ((dy == 1 and dx == 0) or (self._first_move and dy == 2 and dx == 0)):
            self.x, self.y = x, y
            self._first_move = False
        elif self.color == 'чёрный' and ((dy == -1 and dx == 0) or (self._first_move and dy == -2 and dx == 0)):
            self.x, self.y = x, y
            self._first_move = False
        else:
            print("Недопустимый ход для пешки")
Pawn.move = log_call(check_conditions(Pawn.move))
class Knight(Figure, CanCapture):
    def move(self, x, y):
        dx = abs(x - self.x)
        dy = abs(y - self.y)
        if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
            self.x, self.y = x, y
        else:
            print("Недопустимый ход для коня")
Knight.move = log_call(check_conditions(Knight.move))
class Queen(Figure, CanCapture):
    def move(self, x, y):
        dx = x - self.x
        dy = y - self.y
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            self.x, self.y = x, y
        else:
            print("Недопустимый ход для ферзя")
Queen.move = log_call(check_conditions(Queen.move))
class Rook(Figure, CanCapture):
    def move(self, x, y):
        if self.x == x or self.y == y:
            self.x, self.y = x, y
        else:
            print("Недопустимый ход для ладьи")
Rook.move = log_call(check_conditions(Rook.move))
class Bishop(Figure, CanCapture):
    def move(self, x, y):
        dx = x - self.x
        dy = y - self.y
        if abs(dx) == abs(dy):
            self.x, self.y = x, y
        else:
            print("Недопустимый ход для слона")
Bishop.move = log_call(check_conditions(Bishop.move))
class King(Figure, CanCapture):
    def move(self, x, y):
        dx = abs(x - self.x)
        dy = abs(y - self.y)
        if dx <= 1 and dy <= 1:
            self.x, self.y = x, y
        else:
            print("Недопустимый ход для короля")
King.move = log_call(check_conditions(King.move))
class Board:
    def __init__(self):
        self._figures = []
    def add_figure(self, figure):
        if isinstance(figure, ChessPiece):
            self._figures.append(figure)
    def move_figure(self, figure, x, y):
        if figure in self._figures:
            target = self.get_figure_at(x, y)
            if target:
                if isinstance(figure, CanCapture):
                    if figure.capture(target):
                        self._figures.remove(target)
                        figure.move(x, y)
            else:
                figure.move(x, y)
        else:
            print("Фигура не найдена на доске")
    def get_figure_at(self, x, y):
        for figure in self._figures:
            if figure.x == x and figure.y == y:
                return figure
        return None
    def draw(self):
        print("Шахматная доска:")
        for figure in self._figures:
            figure.draw()


ChessPiece.draw = capitalize_output(ChessPiece.draw)
Figure.move = log_call(Figure.move)
Figure.move = check_conditions(Figure.move)

board = Board()
# pawn_white = Pawn(0, 1, 'белый')
# pawn_black = Pawn(0, 6, 'чёрный')
# knight_white = Knight(1, 0, 'белый')
queen = Queen(3, 0, 'белый')
rook = Rook(0, 0, 'чёрный')
bishop = Bishop(2, 0, 'белый')
king = King(4, 0, 'чёрный')
board.add_figure(queen)
board.add_figure(rook)
board.add_figure(bishop)
board.add_figure(king)
# board.add_figure(pawn_white)
# board.add_figure(pawn_black)
# board.add_figure(knight_white)
board.draw()
board.move_figure(queen, 5, 2)
board.move_figure(rook, 0, 5)
board.move_figure(bishop, 4, 2)
board.move_figure(king, 5, 1)
board.draw()
# pawn = Pawn(0, 1, 'белый')
# knight = Knight(1, 0, 'чёрный')
# board = Board()
# board.add_figure(pawn)
# board.add_figure(knight)
# board.draw()
# board.move_figure(pawn, 0, 2)
# board.move_figure(knight, 2, 1)
# board.draw()
# board.move_figure(pawn, 0, 8)
# board.draw()

if __name__ == "__main__":
    print("Шахматные фигуры:")
    for cls in ChessMeta._registry:
        print(cls.__name__)
