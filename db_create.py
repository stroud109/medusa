from model import (
    Base,
    engine,
    User,
    Book,
    BorrowHistory,
    session,
)

from datetime import datetime


def create_tables():
    Base.metadata.create_all(engine)
    u = User(email='steph@test.com', username='steph')
    u.set_password('unicorn')
    session.add(u)
    u2 = User(email='stroud@test2.com', username='stroud')
    u2.set_password('unicorn')
    session.add(u2)
    b = Book(
        title='The Book of Steph',
        amazon_url='www.smstroud.com',
        owner_id=1
    )
    session.add(b)
    b2 = Book(
        title='Stroud\'s Story',
        amazon_url='www.smstroud.com',
        owner_id=1,
        current_borrower=2
    )
    b_h = BorrowHistory(book_id=2, borrower_id=2, date_borrowed=datetime.now)
    # p = Post(title='test post', body='body of a test post.')
    # u.posts.append(p)
    session.add(b)
    session.add(b2)
    b2.borrow_history.append(b_h)
    session.commit()

if __name__ == '__main__':
    create_tables()
