# import datetime  # built-ins
# import random

from flask import (  # stuff i installed with pip
    flash,
    Flask,
    redirect,
    render_template,
    request,
    session,  # app session, not DB session
    url_for,
)

from models import (  # project imports
    authenticate,
    Book,
    # BorrowHistory,
    session as db_session,
    User,
)

app = Flask(__name__)
app.secret_key = "shhhhhhhhhhhhhhsupersecretthing"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
        search_term = request.args.get("search")
        search_results = db_session.query(Book) \
            .filter(Book.name.like("%"+search_term+"%"))
        return render_template(
            'search.html',
            search_results=search_results,
            search_term=search_term,
        )


@app.route("/", methods=["POST"])
def sign_in():
    email = request.form.get("email")
    password = request.form.get("password")
    user_id = authenticate(email, password)
    if user_id is not None:
        flash("loggedin!")

        session['user_id'] = user_id
        print session.get('user_id')
        # return redirect(url_for("view_user_ratings", user_id = user_id))
    else:
        flash("Password or email incorrect. Try again.")
    return redirect(url_for("index"))


@app.route("/users")
def view_all_users():
    user_list = db_session.query(User).limit(20).all()
    # return render_template("user_list.html", users=user_list)
    return render_template("index.html", users=user_list)


@app.route("/users/<user_id>")
def view_user_ratings(user_id):
    pass  # show books user owns, books user borrowing


@app.route("/books")
def view_all_books():
    book_list = db_session.query(Book).limit(20).all()
    # return render_template("book_list.html", books=book_list)
    return render_template("index.html", books=book_list)


@app.route("/books/<book_id>")
def view_book(book_id):
    pass


@app.route("/books/<book_id>", methods=["POST"])
def rate_book(book_id):
    pass


@app.route("/clear")
def session_clear():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
