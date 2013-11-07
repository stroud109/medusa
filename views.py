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
    # BorrowHistory,
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
from flaskext.markdown import Markdown
import config
import forms
import model

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


@app.route("/books/<int:id>")
def view_book(id):
    book = Book.query.get(id)
    return render_template("book.html", book=book)


@app.route("/users")
def view_users():
    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/users/<int:id>")
@login_required
def view_library(id):
    owner_books = db_session.query(Book).filter_by(owner_id=id).all()
    return render_template("library.html", books=owner_books)


@app.route("/add_book")
@login_required
def new_book():
    return render_template("new_book.html")


@app.route("/add_book", methods=["POST"])
@login_required
def add_book():
    form = forms.NewBookForm(request.form)
    print form.title.data
    print form.amazon_url.data
    print "form validation", form.validate()
    if not form.validate():
        flash("Error, all fields are required")
        return render_template("new_book.html")

    new_book = Book(
        title=form.title.data,
        amazon_url=form.amazon_url.data,
        owner_id=session.get("user_id"),
    )
    register_book(new_book)
    # print "current user:", current_user
    # current_user.books.append(new_book)

    model.session.commit()
    model.session.refresh(new_book)

    return redirect(url_for("view_book", id=new_book.id))


@app.route("/borrower_history")  # make sure I query Books and BorrowHistory
def borrower_history(id):
    # borrower = db_session.query(BookHistory).filter_by(borrower_id=id).all()
    # return render_template("library.html", books=book_id)
    pass


@app.route("/book_history")  # make sure I query Books and BorrowHistory
def book_history():
    # books = db_session.query(BookHistory).filter_by(book_id=id).all()
    # return render_template("library.html", books=owner_books)
    pass


@app.route("/login")  # needs work
def login():
    if session.get("user_id"):
        flash("You're already logged in!")
        return render_template("master.html")
    else:
        return render_template("master.html")


@app.route("/login", methods=["POST"])
def authenticate():
    form = forms.LoginForm(request.form)
    # print "Login form validation:", form.validate()
    # print request.method

    if not form.validate():
    # if method not "POST" not form.validate():
        flash("Please input a valid email or password")
        return render_template("master.html")

    email = form.email.data
    password = form.password.data
    print "email", email
    print "password", password

    user = User.query.filter_by(email=email).first()
    # when i fix database, change this to one()

    if not user or not user.authenticate(password):
        flash("Incorrect username or password")
        return render_template("master.html")

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
        return render_template("register.html")
    pass


@app.route("/register", methods=["POST"])
def create_account():
    if session.get("user_id"):
        flash("Your account already exists!")
        return redirect(url_for("index"))

    else:
        form = forms.NewUserForm(request.form)
        print "form validation", form.validate()
        if not form.validate():
            flash("Error, all fields are required")
            return render_template("register.html")

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
