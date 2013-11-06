from wtforms import (
    Form,
    TextField,
    #TextAreaField,
    PasswordField,
    validators,
)


class LoginForm(Form):
    email = TextField("Email", [validators.Required(), validators.Email()])
    password = PasswordField("Password", [validators.Required()])


class NewBookForm(Form):
    title = TextField("title", [validators.Required()])
    amazon_url = validators.URL(require_tld=True, message=u'Invalid URL.')
    #body = TextAreaField("body", [validators.Required()])
