from sqlalchemy import (
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    # backref,
    # relationship,
    scoped_session,
    sessionmaker,
)

engine = create_engine("sqlite:///bookworms.db", echo=False)
session = scoped_session(sessionmaker(bind=engine,
                                      autocommit=False,
                                      autoflush=False,))

Base = declarative_base()
Base.query = session.query_property()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64))
    email = Column(String(64))
    password = Column(String(64))
    zipcode = Column(String(15))


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    amazon_url = Column(String(100), nullable=True)


class BorrowHistory(Base):
    __tablename__ = "borrow_history"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer(), ForeignKey('books.id'))
    owner_id = Column(Integer(), ForeignKey('users.id'))
    borrower_id = Column(Integer(), ForeignKey('users.id'), nullable=True)
    timestamp = Column(DateTime(), nullable=True)  # unix seconds since 1/1/70

    # users = relationship(
    #     "User",
    #     backref=backref("borrow_history", order_by=id),
    # )
    # books = relationship(
    #     "Book",
    #     backref=backref("borrow_history", order_by=id),
    # )


def authenticate(email, password):
    password = hash(password)
    user = session.query(User).filter_by(
        email=email,
        password=password,
    ).first()
    if user is not None:
        return user.id
    else:
        return None


# def add_rating(new_rating):
#     session.add(new_rating)
#     session.commit()


def main():
    """In case we need this for something"""
    pass

if __name__ == "__main__":
    main()
