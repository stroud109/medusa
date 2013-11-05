from flask import (
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
    BorrowHistory
)
from flask.ext.login import (
    LoginManager,
    login_required,
    login_user,
    current_user,
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
    # need to make a book.html, perhaps in place of post.html

# @app.route("/books/new")
# @login_required
# def new_book():
#     return render_template("new_book.html")

# @app.route("/books/new", methods=["POST"])
# @login_required
# def add_book():                    ## this part will depend on barcode reader
#     form = forms.NewPostForm(request.form)
#     if not form.validate():
#         flash("Error, all fields are required")
#         return render_template("new_post.html")

#     post = Post(title=form.title.data, body=form.body.data)
#     current_user.posts.append(post)

#     model.session.commit()
#     model.session.refresh(post)

#     return redirect(url_for("view_post", id=post.id))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def authenticate():
    form = forms.LoginForm(request.form)
    if not form.validate():
        flash("Incorrect username or password")
        return render_template("login.html")

    email = form.email.data
    password = form.password.data

    user = User.query.filter_by(email=email).first()

    if not user or not user.authenticate(password):
        flash("Incorrect username or password")
        return render_template("login.html")

    login_user(user)
    return redirect(request.args.get("next", url_for("index")))


if __name__ == "__main__":
    app.run(debug=True)
