from datetime import datetime
from flaskext.markdown import Markdown
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
    register_book,
    register_user,
    session as db_session,
)
from flask.ext.login import (
    LoginManager,
    login_required,
    login_user,
    # current_user,
)

app = Flask(__name__)
app.config.from_object(config)

# Stuff to make login easier
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# End login stuff

# Adding markdown capability to the app
Markdown(app)


@app.route("/")
def index():
    books = Book.query.all()
    return render_template("index.html", books=books)


@app.route("/books/<int:id>")  # should show borrow history of book
def view_book(id):
    book = Book.query.get(id)
    user_id = session.get("user_id")
    if user_id is not None:
        user_id = int(user_id)
    return render_template("book.html", book=book, user_id=user_id)


# adding this section


@app.route("/books/<int:id>/request", methods=["POST"])
@login_required
def request_book(id):
    book = Book.query.get(id)
    user_id = int(session.get("user_id"))

    if book.owner_id == user_id:
        flash("You can't borrow a book you own")
        return redirect(url_for("view_book", id=id))

    open_user_transactions = BookTransaction.query.filter_by(
        book_id=book.id,
        requester_id=user_id,
        date_confirmed=None).all()

    if open_user_transactions:
        flash("You already have an open transaction with this book")
        return redirect(url_for("view_book", id=id))

    # if not book.current_borrower:  # figure out value of current borrower
    #     model.session.add(book)  # figure out if book is right thing to add
    #     flash("You've successfully requested to borrow this book.")
    # else:
    #     flash("This book is currently checked out.")

    new_transaction = BookTransaction(
        book_id=book.id,
        book_owner_id=book.owner_id,
        requester_id=user_id,  # do i need a date_requested??
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


# end of new section of code


@app.route("/users")
def view_users():
    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/users/<int:id>")
@login_required
def view_library(id):  # should show what books are checked out/in/borrowed
    owner_books = db_session.query(Book).filter_by(owner_id=id).all()
    return render_template("library.html", books=owner_books)


@app.route("/add_book")
@login_required
def new_book():
    form = forms.NewBookForm()
    return render_template("new_book.html", form=form)


@app.route("/add_book", methods=["POST"])
@login_required
def add_book():
    form = forms.NewBookForm(request.form)
    print "form validation", form.validate()
    print form.title.data
    print form.amazon_url.data

    if not form.validate():
        flash("Error, all fields are required")
        return render_template("new_book.html", form=form)

    new_book = Book(
        title=form.title.data,
        amazon_url=form.amazon_url.data,
        owner_id=session.get("user_id"),
    )

    book = db_session.query(Book).filter_by(
        owner_id=new_book.owner_id,
        title=new_book.title
    ).all()

    if book:
        flash("Looks like you already have this book in your library")
        return redirect(url_for("index"))

    register_book(new_book)
    # print "current user:", current_user
    # current_user.books.append(new_book)

    model.session.commit()
    model.session.refresh(new_book)

    return redirect(url_for("view_book", id=new_book.id))


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
    # when i fix database, change this to one()

    if not user or not user.authenticate(password):
        flash("Incorrect username or password")
        return render_template("master.html", form=form)

    login_user(user)
    flash("logged in")
    return redirect(request.args.get("next", url_for("index")))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.pop('user_id', None)
    flash("Logged out")
    return redirect(url_for("index"))


@app.route("/register")
def register():
    if session.get("user_id"):
        flash("You already have an account!")
        return redirect(url_for("index", user_id=session.get("user_id")))
    else:
        form = forms.NewUserForm()
        return render_template("register.html", form=form)
        # return render_template("register.html")


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
    # changed this from first to one

    if user:
        flash("Looks like you already have an account")
        return redirect(url_for("login"))

    new_user = User(
        username=request.form.get("username"),
        email=request.form.get("email"),
    )
    new_user.set_password(request.form.get("password"))

    register_user(new_user)

    model.session.commit()
    model.session.refresh(new_user)
    login_user(new_user)

    flash("You successfully created your account!")
    return redirect(url_for("index", id=new_user.id))


@app.route("/deactivate", methods=["POST"])
def deactivate_accout():
    pass


if __name__ == "__main__":
    app.run(debug=True)
