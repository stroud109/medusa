import config
import bcrypt
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    # Text,
)

from sqlalchemy.orm import (
    sessionmaker,
    scoped_session,
    relationship,
    # backref,
)

from flask.ext.login import UserMixin

engine = create_engine(config.DB_URI, echo=False)
session = scoped_session(sessionmaker(bind=engine,
                         autocommit=False,
                         autoflush=False))

Base = declarative_base()
Base.query = session.query_property()


class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    email = Column(String(64), nullable=False)
    password = Column(String(64), nullable=False)
    salt = Column(String(64), nullable=False)

    # books = relationship("Book", uselist=True)
    # books = relationship("Book")

    def set_password(self, password):
        self.salt = bcrypt.gensalt()
        password = password.encode("utf-8")
        self.password = bcrypt.hashpw(password, self.salt)

    def authenticate(self, password):
        password = password.encode("utf-8")
        return bcrypt.hashpw(
            password,
            self.salt.encode("utf-8"),
        ) == self.password


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    amazon_url = Column(String(100), nullable=True)
    owner_id = Column(Integer(), nullable=False)
    current_borrower_id = Column(Integer(), nullable=True)

    # user = relationship("User", uselist=True)
    # user = relationship("User")
    borrow_history = relationship("BorrowHistory", uselist=True)


class BorrowHistory(Base):
    __tablename__ = "borrow_history"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer(), ForeignKey('books.id'), nullable=False)
    borrower_id = Column(Integer(), ForeignKey('users.id'), nullable=False)
    # timestamp = Column(DateTime, nullable=False, default=datetime.now)
    date_borrowed = Column(DateTime, nullable=False, default=datetime.now)
    date_returned = Column(DateTime, nullable=True, default=datetime.now)
    # unix seconds since 1/1/70

    books = relationship("Book")


def register_book(new_book):
    session.add(new_book)
    session.commit()


def register_user(new_user):
    session.add(new_user)
    session.commit()


def create_tables():
    Base.metadata.create_all(engine)
    u = User(email="test@test.com", username="test")
    u.set_password("unicorn")
    session.add(u)
    u2 = User(email="test2@test2.com", username="test2")
    u2.set_password("unicorn")
    session.add(u2)
    b = Book(
        title="Test Book",
        amazon_url="www.smstroud.com",
        owner_id=1
    )
    session.add(b)
    b2 = Book(
        title="Test Book2",
        amazon_url="www.smstroud.com",
        owner_id=2,
    )
    session.add(b2)
    session.commit()

if __name__ == "__main__":
    create_tables()
