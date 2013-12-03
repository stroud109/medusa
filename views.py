from datetime import datetime
from flaskext.markdown import Markdown
from flask.ext.babel import Babel
import config
import forms
import model

import json

from flask import (
    abort,
    Flask,
    render_template,
    redirect,
    request,
    g,
    session,
    url_for,
    flash,
)
from model import (
    User,
    Book,
    BookTransaction,
    BookInfo,
    SearchTerm,
    session as db_session,
)
from flask.ext.login import (
    LoginManager,
    login_required,
    login_user,
    # current_user,
)

from sqlalchemy import or_

from amazon_search import get_book_info_from_ean
from search import index_new_book_info, recreate_index

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


# @app.context_processor
# def inject_user():
#     user = None
#     user_id = session.get("user_id")
#     if user_id is not None:
#         user = User.query.get(user_id)
#     return {"user": user}


@app.before_request
def attach_user_to_global_object():
    user = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = User.query.get(user_id)
    g.user = user


# Adding markdown capability to the app
Markdown(app)

AVATAR_URLS = [
    "/static/img/avatars/cat.png",
    "/static/img/avatars/spaceman.png",
    "/static/img/avatars/lion.png",
    "/static/img/avatars/sleepy.png",
    "/static/img/avatars/veniceunderwater.png",
    "/static/img/avatars/butterowl.png",
    "/static/img/avatars/sloth.png",
    "/static/img/avatars/queen.png",
    "/static/img/avatars/oldman.png",
    "/static/img/avatars/sheep.png",
]


@app.route("/")
def index():

    books = None
    open_user_transactions = None
    open_transactions_on_users_books = None

    if g.user:
        # user_id = session.get("user_id")
        books = Book.query.filter(
            Book.owner_id != g.user.id,
        ).all()

        # transactions = BookTransaction.query.all()

        open_user_transactions = BookTransaction.query.filter(
            BookTransaction.requester_id == g.user.id,
            BookTransaction.date_confirmed == None,
        ).all()

        open_transactions_on_users_books = BookTransaction.query.filter(
            BookTransaction.book_owner_id == g.user.id,
            BookTransaction.date_confirmed == None,
        ).all()

        print "LOOK HERE"
        print "books", books

    else:
        books = Book.query.all()

    return render_template(
        "index.html",
        books=books,
        # transactions=transactions,
        open_user_transactions=open_user_transactions,
        open_transactions_on_users_books=open_transactions_on_users_books,
    )


@app.route("/keyword_search/recreate_index")
def recreate_search_index():
    recreate_index()
    return "success", 200


@app.route("/keyword_search")  # SEARCH BOOKWORMS FOR A BOOK
def keyword_search():

    searched_for = request.args.get('q')

    tokens = []

    if not searched_for or searched_for == "":
        flash('Please enter a valid search term')
        return redirect(url_for("index"))
    else:
    # if searched_for is not None and searched_for != "":
        tokens = searched_for.split(' ')

    # figure out filter_by token in array
    # figure out how to use an in clause in sqlalchemy
    search_results = SearchTerm.query.filter(
        SearchTerm.token.in_(tokens)
        ).all()
    # make the search results a flat, unique list of book info ids

    document_ids = []
    for result in search_results:
        document_ids += json.loads(result.document_ids)

    unique_ids = set(document_ids)
    print "document ids HERE", document_ids
    print "unique ids HERE", unique_ids

    books = Book.query.filter(
        Book.book_info_id.in_(unique_ids)
        ).all()

    return render_template(
        "keyword_search.html",
        searched_for=searched_for,
        # search_results=search_results,
        unique_ids=unique_ids,
        # book_title=book_title,
        books=books,
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
        model.session.refresh(book_info)
        index_new_book_info(book_info)

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
        owner_id=g.user.id,
        book_info_id=book_info_id,
    ).all()

    if book:
        flash("Looks like you already have this book in your library")
        return redirect(url_for("view_book", id=book.id))  # CHECK THIS

    new_book = Book(
        title=book_info.title,
        owner_id=g.user.id,
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

    if not book:
        abort(404)

    # user_id = g.user.id
    # print book
    # print book.book_info[0].isbn

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

    open_user_transaction = None

    if g.user:
        open_user_transaction = book.get_open_transaction_for_user(g.user.id)

    return render_template(
        "book.html",
        book=book,
        transaction_in_progress=transaction_in_progress,
        open_user_transaction=open_user_transaction,
        book_requests=book_requests,
        # returned_book=returned_book,
    )


@app.route("/books/<int:id>/request", methods=["POST"])
@login_required
def request_book(id):
    book = Book.query.get(id)

    if not book:
        abort(404)

    user_id = int(g.user.id)

    if book.owner_id == user_id:
        flash("You can't borrow a book you own")
        return redirect(url_for("view_book", id=id))

    open_user_transactions = book.get_open_transaction_for_user(user_id)

    if open_user_transactions:
        flash("You already have an open transaction with this book")
        # return redirect(url_for("view_book", id=id))
        return redirect(url_for("index"))

    new_transaction = BookTransaction(
        book_id=book.id,
        book_owner_id=book.owner_id,
        requester_id=user_id,
    )
    # flash("You've successfully requested this book")
    model.session.add(new_transaction)
    model.session.commit()
    # model.session.refresh(book)
    # return redirect(url_for("view_book", id=id))
    return redirect(url_for("view_book", id=book.id))


@app.route("/books/<int:id>/borrow", methods=["POST"])
@login_required
def declare_borrowed(id):
    transaction = BookTransaction.query.get(id)

    if not transaction:
        abort(404)

    # print type(transaction.book.owner_id)
    # print type(g.user.id)

    if transaction.book.owner_id == g.user.id:
        if transaction.date_requested is not None:
            if transaction.book.current_borrower_id is None:
                transaction.book.current_borrower_id = transaction.requester_id
                transaction.date_borrowed = datetime.now()
                # flash("You've declared that your book is being borrowed")
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
    # return redirect(url_for("view_book", id=transaction.book.id))
    return redirect(url_for("view_book", id=transaction.book_id))


@app.route("/books/<int:id>/return", methods=["POST"])
@login_required
def return_book(id):
    transaction = BookTransaction.query.get(id)

    if not transaction:
        abort(404)

    if transaction.book.owner_id != g.user.id:
        if transaction.book.current_borrower_id == g.user.id:
            # ^Revisit this line to avoid future current_borrower_id bugs
            if transaction.date_borrowed is not None:
                if transaction.date_returned is not None:
                    flash("This book has already been returned")
                else:
                    transaction.date_returned = datetime.now()
                    # flash("You've marked this book as returned")
                    model.session.add(transaction)
                    model.session.commit()
            else:
                flash("Book must be borrowed before it's returned")
        else:
            flash("You can't return a book that you aren't borrowing")
    else:
        flash("You can't return a book you already own")

    # return redirect(url_for("view_book", id=transaction.book.id))
    return redirect(url_for("view_book", id=transaction.book_id))


@app.route("/books/<int:id>/confirmation", methods=["POST"])
@login_required
def confirm_book_returned(id):
    transaction = BookTransaction.query.get(id)

    if not transaction:
        abort(404)

    user_id = int(g.user.id)

    if transaction.book.owner_id == user_id:
        # if transaction.date_returned is not None:
        if transaction.book.current_borrower_id is not None:
            transaction.book.current_borrower_id = None
            transaction.date_confirmed = datetime.now()
            # flash("You've confirmed that your book has been returned to you")
            model.session.add(transaction)
            model.session.add(transaction.book)
            model.session.commit()
        else:
            flash("You've already confirmed this book has been returned")
        # else:
        #     flash("Book must be marked as returned before you confirm")
    else:
        flash("You can only confirm returns on books you own")
    # model.session.refresh(book)
    # return redirect(url_for("view_book", id=transaction.book.id))
    return redirect(url_for("view_book", id=transaction.book_id))


@app.route("/login")
def login():
    if g.user:
        flash("You're already logged in!")
        return render_template("login.html")
    else:
        form = forms.LoginForm()
        return render_template("login.html", form=form)


@app.route("/login", methods=["POST"])
def authenticate():
    form = forms.LoginForm(request.form)
    # print "Login form validation:", form.validate()
    # print request.method

    if not form.validate():
    # if method not "POST" not form.validate():
        flash("Please input a valid email or password")
        return render_template("login.html", form=form)

    email = form.email.data
    password = form.password.data
    # print "email", email
    # print "password", password

    user = User.query.filter_by(email=email).first()

    if not user or not user.authenticate(password):
        flash("Incorrect username or password")
        return render_template("login.html", form=form)

    login_user(user)
    flash("Welcome, %s" % user.username)
    return redirect(request.args.get("next", url_for("index")))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.pop('user_id', None)
    flash("Goodbye, %s" % g.user.username)
    return redirect(url_for("index"))


@app.route("/register")
def register():
    if g.user:
        flash("You already have an account!")
        return redirect(url_for("index", user_id=g.user.id))
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
    username = form.username.data
    username_or_email = or_(User.email == email, User.username == username)
    user = User.query.filter(username_or_email).first()

    if user:
        if user.email == email:
            form.email.errors = ["There's already an account with this email"]
        if user.username == username:
            form.username.errors = ["There's aleady an account with this username"]
        # return redirect(url_for("create_account"))
        return render_template("register.html", form=form)

    new_user = User(
        username=username,
        email=email,
        avatar_url=AVATAR_URLS[6],
    )
    new_user.set_password(request.form.get("password"))

    model.session.add(new_user)

    model.session.commit()
    model.session.refresh(new_user)
    login_user(new_user)

    flash("You've successfully created an account. Welcome!")
    # return redirect(url_for("index", id=new_user.id))
    return redirect(url_for("edit_user", id=new_user.id))


@app.route("/users")
def view_users():
    users = User.query.all()

    # for user in users:
    #     num_books = len(user.books)
        # print "%s has %s many books" % (user.username, len(user.books))
    return render_template("users.html", users=users)


@app.route("/users/<int:id>/edit")
@login_required
def edit_user(id):

    owner = User.query.get(id)

    if not owner:
        abort(404)

    return render_template(
        "edit_user.html",
        owner=owner,
        avatar_urls=AVATAR_URLS,
    )


@app.route("/users/<int:id>", methods=["POST"])
@login_required
def update_user(id):
    """
    Takes a POSTed form and updates the given user with values
    from the form.
    """
    # Check to make sure the session user is the
    # owner of the user model they are trying to update
    if int(id) != g.user.id:
        flash('You can\'t update other user accounts')
        return redirect(url_for('view_library', id=g.user.id))

    # Check to make sure the user we are trying to
    # update actually exists

    # Start setting attributes on the user
    # For right now, we only have one attribute we care about
    form = forms.UserForm(request.form)

    should_save = False

    if form.location.data:
        g.user.location = form.location.data
        should_save = True

    if form.avatar_url.data:
        g.user.avatar_url = form.avatar_url.data
        should_save = True

    if should_save:
        model.session.add(g.user)
        model.session.commit()

    # Finally, tell the browser to redirect the user
    # to their library page
    flash('You updated your account successfully')
    return redirect(url_for('view_library', id=g.user.id))


@app.route("/users/<int:id>", methods=["GET"])
@login_required
def view_library(id):  # should show what books are checked out/in/borrowed
    # owner_books = db_session.query(Book).filter_by(owner_id=id).all()
    owner = User.query.get(id)

    # user_requests = BookTransaction.query.filter(
    #     BookTransaction.requester_id == owner.id,
    # ).all()

    if not owner:
        abort(404)

    current_user_requests = BookTransaction.query.filter(
        BookTransaction.requester_id == owner.id,
        BookTransaction.date_confirmed == None,
    ).all()

    past_user_requests = BookTransaction.query.filter(
        BookTransaction.requester_id == owner.id,
        BookTransaction.date_confirmed != None,
    ).all()

    return render_template(
        "library.html",
        owner=owner,
        # user_requests=user_requests,
        current_user_requests=current_user_requests,
        past_user_requests=past_user_requests,
    )


@app.route("/books/<int:id>/delete", methods=["POST"])
@login_required
def remove_book(id):
    book = Book.query.get(id)

    if book.owner.id == g.user.id:
        flash("%s was successfully deleted from your library" % book.title)
        model.session.delete(book)
        BookTransaction.query.filter_by(
            book_id=book.id
        ).delete()
        model.session.commit()

    return redirect(url_for("view_library", id=g.user.id))


@app.route("/deactivate", methods=["POST"])  # add this for better UX
def deactivate_accout():
    pass


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )
