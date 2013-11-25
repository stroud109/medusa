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

    books = relationship("Book", uselist=True)

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
    owner_id = Column(Integer(), ForeignKey('users.id'), nullable=False)
    current_borrower_id = Column(Integer(), nullable=True)
    book_info_id = Column(Integer(), ForeignKey('book_info.id'), nullable=False)
    # add number_copies = Column(Integer(), nullable=False) ??

    book_transactions = relationship("BookTransaction", uselist=True)
    book_info = relationship("BookInfo", uselist=False)
    owner = relationship("User", foreign_keys=owner_id)
    # current_borrower = relationship("User")

    def get_open_transaction_for_user(self, user_id):
        return BookTransaction.query.filter_by(
            requester_id=user_id,
            date_confirmed=None,
            book_id=self.id
        ).first()


class BookInfo(Base):
    __tablename__ = "book_info"

    id = Column(Integer, primary_key=True)
    ean = Column(String(17), nullable=True)
    isbn = Column(String(13), nullable=True)
    title = Column(String(100), nullable=False)
    author = Column(String(100), nullable=False)
    number_pages = Column(Integer(), nullable=True)
    genre = Column(String(50), nullable=True)
    image_url = Column(String(300), nullable=True)
    editorial_review = Column(String(10000), nullable=True)

    books = relationship("Book", uselist=True)


class BookTransaction(Base):
    __tablename__ = "book_transactions"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer(), ForeignKey('books.id'), nullable=False)
    book_owner_id = Column(Integer(), ForeignKey('users.id'), nullable=False)
    requester_id = Column(Integer(), ForeignKey('users.id'), nullable=False)
    date_requested = Column(DateTime, nullable=False, default=datetime.now)
    date_borrowed = Column(DateTime, nullable=True)
    date_returned = Column(DateTime, nullable=True)
    date_confirmed = Column(DateTime, nullable=True)

    book = relationship("Book")
    book_owner = relationship("User", foreign_keys=book_owner_id)
    requester = relationship("User", foreign_keys=requester_id)

    # def user_can_declare_borrowed(self, user_id):
    #     return (
    #         user_id == self.book_owner_id and
    #         self.book.current_borrower_id is None and
    #         self.date_requested is not None and
    #         self.date_borrowed is None and
    #         self.date_confirmed is None
    #     )

    def get_state(self):
        state = None
        if self.date_borrowed:
            if self.date_returned:
                if self.date_confirmed:
                    state = "closed"
                else:
                    state = "returned"
            else:
                state = "borrowed"
        else:
            state = "requested"

        return state


class SearchTerm(Base):
    __tablename__ = "search_terms"
    id = Column(Integer, primary_key=True)
    token = Column(String(1000), nullable=False)
    num_results = Column(Integer(), nullable=False)
    document_ids = Column(String(1000), nullable=False)


def register_book(new_book):
    session.add(new_book)
    session.commit()


def register_user(new_user):
    session.add(new_user)
    session.commit()


def create_tables():
    Base.metadata.create_all(engine)
    # u = User(email="test@test.com", username="test")
    # u.set_password("unicorn")
    # session.add(u)
    # print "adding user1"
    # u2 = User(email="test2@test2.com", username="test2")
    # u2.set_password("unicorn")
    # session.add(u2)
    # print "adding user2"
    # b_i1 = BookInfo(title="test book", author="test author")
    # session.add(b_i1)
    # print "adding book info 1"
    # b_i2 = BookInfo(title="test book2", author="test author2")
    # session.add(b_i2)
    # print "adding book info 2"

    # b = Book(
    #     title="test book",
    #     owner_id=1,
    #     book_info_id=1,
    # )
    # session.add(b)
    # print "adding book1"
    # b2 = Book(
    #     title="test book2",
    #     owner_id=2,
    #     book_info_id=2,
    # )
    # session.add(b2)
    # print "adding book2"
    # session.commit()
    # print "committing users, book info and books 1 and 2"

if __name__ == "__main__":
    create_tables()
    print "tables should be created now"
