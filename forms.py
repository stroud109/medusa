from wtforms import (
    Form,
    TextField,
    #TextAreaField,
    PasswordField,
    validators,
)


class LoginForm(Form):
    # email = TextField("Email", [validators.Required(), validators.Email()])
    email = TextField("Email", [validators.Required(), validators.Email()])
    password = PasswordField("Password", [validators.Required()])


class NewBookForm(Form):
    title = TextField("Title", [validators.Required()])
    # amazon_url = TextField("amazon_URL", [validators.Required(), validators.URL()])
    amazon_url = TextField("Amazon Url", [validators.Required(), validators.URL()])
    # amazon_url = validators.URL(require_tld=True, message=u'Invalid URL.')
    # body = TextAreaField("body", [validators.Required()])


class NewUserForm(Form):
    username = TextField("Username", [validators.Required()])
    email = TextField("Email", [validators.Required(), validators.Email()])
    password = PasswordField("Password", [validators.Required()])
