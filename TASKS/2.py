import abc
import asyncio
import threading
import time
from abc import abstractmethod
from functools import wraps
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ChessPieceModel(Base):
    __tablename__ = 'chess_pieces'
    id = Column(Integer, primary_key=True)
    type = Column(String(255))
    x = Column(Integer)
    y = Column(Integer)
    color = Column(String(255))


engine = create_engine('mysql+pymysql://root:12345@localhost/chess')

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
class OutOfBoardError(Exception):
    def __init__(self, message="Фигура выходит за пределы доски"):
        self.message = message
        super().__init__(self.message)
class InvalidMoveError(Exception):
    def __init__(self, message="Недопустимый ход"):
        self.message = message
        super().__init__(self.message)
def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        #print(f"Вызов {func.__name__}...")
        result = func(*args, **kwargs)
        end_time = time.time()
        #print(f"{func.__name__} завершен за {end_time - start_time:.2f} секунд")
        return result
    return wrapper
def check_conditions(func):
    def wrapper(self, x, y, *args, **kwargs):
        if not (0 <= x <= 7 and 0 <= y <= 7):
            raise OutOfBoardError("Целевая позиция за пределами поля")
        result = func(self, x, y, *args, **kwargs)
        if not (0 <= self.x <= 7 and 0 <= self.y <= 7):
            raise OutOfBoardError("Фигура оказалась за пределами поля после хода")
        return result
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
    def capture(self, other, board):
        if isinstance(other, ChessPiece) and other.color != self.color:
            print(f"{self.__class__.__name__} победил {other.__class__.__name__}")
            session.add(ChessPieceModel(
                type=other.__class__.__name__,
                x=other.x,
                y=other.y,
                color=other.color
            ))
            session.commit()
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
        try:
            dx = x - self.x
            dy = y - self.y
            if self.color == 'белый' and ((dy == 1 and dx == 0) or (self._first_move and dy == 2 and dx == 0)):
                self.x, self.y = x, y
                self._first_move = False
            elif self.color == 'чёрный' and ((dy == -1 and dx == 0) or (self._first_move and dy == -2 and dx == 0)):
                self.x, self.y = x, y
                self._first_move = False
            else:
                raise InvalidMoveError("Недопустимый ход для пешки")
        except OutOfBoardError as e:
            print(f"Ошибка: {e}")
        except InvalidMoveError as e:
            print(f"Ошибка: {e}")
Pawn.move = log_call(check_conditions(Pawn.move))
class Knight(Figure, CanCapture):
    def move(self, x, y):
        try:
            dx = abs(x - self.x)
            dy = abs(y - self.y)
            if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
                self.x, self.y = x, y
            else:
                raise InvalidMoveError("Недопустимый ход для коня")
        except OutOfBoardError as e:
            print(f"Ошибка: {e}")
        except InvalidMoveError as e:
            print(f"Ошибка: {e}")
Knight.move = log_call(check_conditions(Knight.move))
class Queen(Figure, CanCapture):
    def move(self, x, y):
        try:
            dx = x - self.x
            dy = y - self.y
            if dx == 0 or dy == 0 or abs(dx) == abs(dy):
                self.x, self.y = x, y
            else:
                raise InvalidMoveError("Недопустимый ход для ферзя")
        except OutOfBoardError as e:
            print(f"Ошибка: {e}")
        except InvalidMoveError as e:
            print(f"Ошибка: {e}")
Queen.move = log_call(check_conditions(Queen.move))
class Rook(Figure, CanCapture):
    def move(self, x, y):
        try:
            if self.x == x or self.y == y:
                self.x, self.y = x, y
            else:
                raise InvalidMoveError("Недопустимый ход для ладьи")
        except OutOfBoardError as e:
            print(f"Ошибка: {e}")
        except InvalidMoveError as e:
            print(f"Ошибка: {e}")
Rook.move = log_call(check_conditions(Rook.move))
class Bishop(Figure, CanCapture):
    def move(self, x, y):
        try:
            dx = x - self.x
            dy = y - self.y
            if abs(dx) == abs(dy):
                self.x, self.y = x, y
            else:
                raise InvalidMoveError("Недопустимый ход для слона")
        except OutOfBoardError as e:
            print(f"Ошибка: {e}")
        except InvalidMoveError as e:
            print(f"Ошибка: {e}")
Bishop.move = log_call(check_conditions(Bishop.move))
class King(Figure, CanCapture):
    def move(self, x, y):
        try:
            dx = abs(x - self.x)
            dy = abs(y - self.y)
            if dx <= 1 and dy <= 1:
                self.x, self.y = x, y
            else:
                raise InvalidMoveError("Недопустимый ход для короля")
        except OutOfBoardError as e:
            print(f"Ошибка: {e}")
        except InvalidMoveError as e:
            print(f"Ошибка: {e}")
King.move = log_call(check_conditions(King.move))
class Board:
    def __init__(self):
        self._figures = []
    def add_figure(self, figure):
        if isinstance(figure, ChessPiece):
            self._figures.append(figure)
    def is_position_occupied_by_same_color(self, figure, x, y):
        target = self.get_figure_at(x, y)
        return target and target.color == figure.color
    def move_figure(self, figure, x, y):
        if not (0 <= x <= 7 and 0 <= y <= 7):
            print("Невозможно сделать ход: целевая позиция за пределами доски.")
            return
        if figure in self._figures:
            if self.is_position_occupied_by_same_color(figure, x, y):
                raise InvalidMoveError("Целевая позиция занята фигурой того же цвета")
            target = self.get_figure_at(x, y)
            if target:
                if isinstance(figure, CanCapture):
                    if figure.capture(target, self):
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
    def move_figure_in_thread(self, figure, x, y):
        thread = threading.Thread(target=self.move_figure, args=(figure, x, y))
        thread.start()
        thread.join()
    async def move_figure_async(self, figure, x, y):
            if figure in self._figures:
                target = self.get_figure_at(x, y)
                if target:
                    if isinstance(figure, CanCapture):
                        if figure.capture(target):
                            self._figures.remove(target)
                            await asyncio.sleep(0)
                            figure.move(x, y)
                else:
                    await asyncio.sleep(0)
                    figure.move(x, y)
            else:
                print("Фигура не найдена на доске")

    def save_to_db(self):
        session.query(ChessPieceModel).delete()
        for figure in self._figures:
            piece_record = ChessPieceModel(
                type=figure.__class__.__name__,
                x=figure.x,
                y=figure.y,
                color=figure.color
            )
            session.add(piece_record)
        session.commit()

    def load_from_db(self):
        session = Session()
        figures_data = session.query(ChessPieceModel).all()
        for figure_data in figures_data:
            figure = self.create_figure(figure_data.type, figure_data.x, figure_data.y, figure_data.color)
            self.add_figure(figure)
        session.close()
    def create_figure(self, type, x, y, color):
        if type == 'Pawn':
            return Pawn(x, y, color)
        elif type == 'Knight':
            return Knight(x, y, color)
        elif type == 'Bishop':
            return Bishop(x, y, color)
        elif type == 'Rook':
            return Rook(x, y, color)
        elif type == 'Queen':
            return Queen(x, y, color)
        elif type == 'King':
            return King(x, y, color)
        else:
            raise ValueError(f"Неизвестный тип фигуры: {type}")
ChessPiece.draw = capitalize_output(ChessPiece.draw)
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
    board = Board()
    pawn_white = Pawn(0, 1, 'белый')
    pawn_black = Pawn(0, 6, 'чёрный')
    knight_white = Knight(1, 0, 'белый')
    queen_white = Queen(3, 0, 'белый')
    rook_black = Rook(0, 0, 'чёрный')
    bishop_white = Bishop(2, 0, 'белый')
    king_black = King(4, 0, 'чёрный')
    board.add_figure(pawn_white)
    board.add_figure(pawn_black)
    board.add_figure(knight_white)
    board.add_figure(queen_white)
    board.add_figure(rook_black)
    board.add_figure(bishop_white)
    board.add_figure(king_black)
    board.draw()
    board.move_figure_in_thread(pawn_white, 0, 3)
    board.move_figure_in_thread(pawn_black, 0, 4)
    board.move_figure_in_thread(knight_white, 2, 2)
    board.move_figure_in_thread(queen_white, 5, 2)
    board.move_figure_in_thread(rook_black, 0, 5)
    board.move_figure_in_thread(bishop_white, 4, 2)
    board.move_figure_in_thread(king_black, 5, 1)
    board.move_figure(pawn_black, 0, 3)
    time.sleep(1)
    board.draw()