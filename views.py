from datetime import datetime
from flaskext.markdown import Markdown
from flask.ext.babel import Babel
import config
import forms
import model

from flask import (
    Flask,
    render_template,
    redirect,
    request,
    # g,
    session,
    url_for,
    flash,
)
from model import (
    User,
    Book,
    BookTransaction,
    BookInfo,
    # register_book,
    # register_user,
    session as db_session,
)
from flask.ext.login import (
    LoginManager,
    login_required,
    login_user,
    # current_user,
)

from amazon_search import get_book_info_from_ean

app = Flask(__name__)
app.config.from_object(config)
babel = Babel(app, configure_jinja=True)

# Stuff to make login easier
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# End login stuff


@app.context_processor
def inject_user():
    user = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = User.query.get(user_id)
    return {"user": user}


# Adding markdown capability to the app
Markdown(app)


@app.route("/")  # CHANGE THIS SO USER CAN ONLY SEE OPEN REQUESTS
def index():

    user_id = session.get("user_id")
    books = Book.query.filter(
        Book.owner_id != user_id,
    ).all()
    # transactions = BookTransaction.query.all()

    open_user_requests = BookTransaction.query.filter(
        BookTransaction.requester_id == user_id,
        BookTransaction.date_confirmed == None,
    ).all()

    users_open_book_transactions = BookTransaction.query.filter(
        BookTransaction.book_owner_id == user_id,
        BookTransaction.date_confirmed == None,
    ).all()

    print "LOOK HERE"
    print "books", books
    return render_template(
        "index.html",
        books=books,
        # transactions=transactions,
        open_user_requests=open_user_requests,
        users_open_book_transactions=users_open_book_transactions,
    )


@app.route("/search")  # camera and user input form live here
def search():
    return render_template("search.html")


@app.route("/results")  # test on this EAN 0076783007994
def results():  # use this page for pre-DB commit search results
    # http://domain/path?query=parameter#hash
    ean = request.args.get('ean')  # checks if url query params has 'ean'
    if not ean:  # checking for truthiness rather than actual existance
        return redirect(url_for("search"))
    # if user pushes 'confirm' button, add and commit book_info item
    # adds 'book' to book_info library

    book_info = db_session.query(BookInfo).filter_by(ean=ean).first()

    # temp = get_book_info_from_ean(ean)

    if not book_info:
        book_info = get_book_info_from_ean(ean)  # see amazon_search.py
        model.session.add(book_info)
        model.session.commit()

    return render_template("results.html", book_info=book_info)


@app.route("/add_book/<book_info_id>", methods=["POST"])
# adds book to user library
@login_required
def add_book(book_info_id):
    book_info = db_session.query(BookInfo).filter_by(
        id=book_info_id,
    ).first()

    if not book_info:
        return redirect(url_for("search"))

    book = db_session.query(Book).filter_by(
        owner_id=session.get("user_id"),
        book_info_id=book_info_id,
    ).all()

    if book:
        flash("Looks like you already have this book in your library")
        return redirect(url_for("index"))  # change this

    new_book = Book(
        title=book_info.title,
        owner_id=session.get("user_id"),
        book_info_id=book_info_id,
    )

    model.session.add(new_book)
    # print "current user:", current_user
    # current_user.books.append(new_book)

    model.session.commit()
    model.session.refresh(new_book)

    return redirect(url_for("view_book", id=new_book.id))


@app.route("/books/<int:id>")  # should show borrow history of book
def view_book(id):
    book = Book.query.get(id)
    user_id = session.get("user_id")
    # print book
    # print book.book_info[0].isbn

    if user_id is not None:
        user_id = int(user_id)

    # can_request_book: user_id != owner_id and no open transaction for user
    # can_declare_borrowed: if transaction.get_state() == "requested"
    # and if no other open transactions
    # can_return_book: if transaction.get_state() == "borrowed"
    # and if no other open transactions
    # can_confirm_returned: if transaction.get_state() == "returned"
    # and if no other open transactions

    # need to build open transaction where transaction is borrowed or returned,
    # but not closed or requested
    # this function should not apply to specific user

    # current transaction that's in-progess based on 2nd and 4th state
    transaction_in_progress = BookTransaction.query.filter(
        BookTransaction.date_borrowed != None,
        BookTransaction.date_confirmed == None,
        BookTransaction.book_id == book.id,
    ).first()

    book_requests = BookTransaction.query.filter(
        BookTransaction.book_id == book.id,
        BookTransaction.date_requested != None,
        BookTransaction.date_borrowed == None,
    ).all()

    # returned_book = BookTransaction.query.filter(
    #     BookTransaction.book_id == book.id,
    #     BookTransaction.date_borrowed != None,
    #     BookTransaction.date_returned == None,
    # ).first()

    return render_template(
        "book.html",
        book=book,
        user_id=user_id,
        transaction_in_progress=transaction_in_progress,
        open_user_transaction=book.get_open_transaction_for_user(user_id),
        book_requests=book_requests,
        # returned_book=returned_book,
    )


@app.route("/books/<int:id>/request", methods=["POST"])
@login_required
def request_book(id):
    book = Book.query.get(id)
    user_id = int(session.get("user_id"))

    if book.owner_id == user_id:
        flash("You can't borrow a book you own")
        return redirect(url_for("view_book", id=id))

    open_user_transactions = book.get_open_transaction_for_user(user_id)

    if open_user_transactions:
        flash("You already have an open transaction with this book")
        return redirect(url_for("view_book", id=id))

    new_transaction = BookTransaction(
        book_id=book.id,
        book_owner_id=book.owner_id,
        requester_id=user_id,
    )

    model.session.add(new_transaction)
    model.session.commit()
    # model.session.refresh(book)
    return redirect(url_for("view_book", id=id))


@app.route("/books/<int:id>/borrow", methods=["POST"])
@login_required
def declare_borrowed(id):
    transaction = BookTransaction.query.get(id)
    user_id = int(session.get("user_id"))
    print type(transaction.book.owner_id)
    print type(user_id)

    if transaction.book.owner_id == user_id:
        if transaction.date_requested is not None:
            if transaction.book.current_borrower_id is None:
                transaction.book.current_borrower_id = transaction.requester_id
                transaction.date_borrowed = datetime.now()
                flash("You've declared that this book as borrowed")
                model.session.add(transaction)
                model.session.add(transaction.book)
                model.session.commit()

            else:
                flash("This book already has a borrower")
        else:
            flash("Book must be requested before it's borrowed")
    else:
        flash("You must own a book to declare that it's been borrowed")
    # model.session.refresh(book)
    return redirect(url_for("view_book", id=transaction.book.id))


@app.route("/books/<int:id>/return", methods=["POST"])
@login_required
def return_book(id):
    transaction = BookTransaction.query.get(id)
    user_id = int(session.get("user_id"))

    if transaction.book.owner_id != user_id:
        if transaction.book.current_borrower_id == user_id:
            if transaction.date_borrowed is not None:
                if transaction.date_returned is not None:
                    flash("This book has already been returned")
                else:
                    transaction.date_returned = datetime.now()
                    model.session.add(transaction)
                    model.session.commit()
                    flash("You have marked this book as returned")
            else:
                flash("Book must be borrowed before it's returned")
        else:
            flash("You can't return a book that you aren't borrowing.")
    else:
        flash("You can't return a book you already own")

    return redirect(url_for("view_book", id=transaction.book.id))


@app.route("/books/<int:id>/confirmation", methods=["POST"])
@login_required
def confirm_book_returned(id):
    transaction = BookTransaction.query.get(id)
    user_id = int(session.get("user_id"))

    if transaction.book.owner_id == user_id:
        if transaction.date_returned is not None:
            if transaction.book.current_borrower_id is not None:
                transaction.book.current_borrower_id = None
                transaction.date_confirmed = datetime.now()
                model.session.add(transaction)
                model.session.add(transaction.book)
                model.session.commit()
            else:
                flash("You've already confirmed this book has been returned")
        else:
            flash("Book must be marked as returned before you confirm")
    else:
        flash("You can only confirm returns on books you own")
    # model.session.refresh(book)
    return redirect(url_for("view_book", id=transaction.book.id))


@app.route("/login")
def login():
    if session.get("user_id"):
        flash("You're already logged in!")
        return render_template("master.html")
    else:
        form = forms.LoginForm()
        return render_template("master.html", form=form)


@app.route("/login", methods=["POST"])
def authenticate():
    form = forms.LoginForm(request.form)
    # print "Login form validation:", form.validate()
    # print request.method

    if not form.validate():
    # if method not "POST" not form.validate():
        flash("Please input a valid email or password")
        return render_template("master.html", form=form)

    email = form.email.data
    password = form.password.data
    # print "email", email
    # print "password", password

    user = User.query.filter_by(email=email).one()

    if not user or not user.authenticate(password):
        flash("Incorrect username or password")
        return render_template("master.html", form=form)

    login_user(user)
    flash("Welcome, %s" % user.username)
    return redirect(request.args.get("next", url_for("index")))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    user_id = session.pop('user_id', None)
    user = User.query.get(user_id)
    flash("Goodbye, %s" % user.username)
    return redirect(url_for("index"))


@app.route("/register")
def register():
    if session.get("user_id"):
        flash("You already have an account!")
        return redirect(url_for("index", user_id=session.get("user_id")))
    else:
        form = forms.NewUserForm()
        return render_template("register.html", form=form)


@app.route("/register", methods=["POST"])
def create_account():
    # if session.get("user_id"):
    #     flash("Your account already exists!")
    #     return redirect(url_for("index"))

    form = forms.NewUserForm(request.form)
    print "form validation", form.validate()
    if not form.validate():
        flash("Error, all fields are required")
        return render_template("register.html", form=form)

    email = form.email.data
    user = User.query.filter_by(email=email).one()

    if user:
        flash("Looks like you already have an account")
        return redirect(url_for("login"))

    new_user = User(
        username=request.form.get("username"),
        email=request.form.get("email"),
    )
    new_user.set_password(request.form.get("password"))

    model.session.add(new_user)

    model.session.commit()
    model.session.refresh(new_user)
    login_user(new_user)

    flash("You successfully created your account!")
    return redirect(url_for("index", id=new_user.id))


@app.route("/users")
def view_users():
    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/users/<int:id>")
@login_required
def view_library(id):  # should show what books are checked out/in/borrowed
    # owner_books = db_session.query(Book).filter_by(owner_id=id).all()
    owner = User.query.get(id)

    user_requests = BookTransaction.query.filter(
        BookTransaction.requester_id == owner.id,
    ).all()

    return render_template(
        "library.html",
        owner=owner,
        user_requests=user_requests
    )


@app.route("/deactivate", methods=["POST"])  # add this for better UX
def deactivate_accout():
    pass


if __name__ == "__main__":
    app.run(debug=True)
