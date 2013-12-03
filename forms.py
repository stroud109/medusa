from wtforms import (
    Form,
    TextField,
    #TextAreaField,
    PasswordField,
    validators,
    widgets,
)


class TextInput(widgets.TextInput):
    def __call__(self, field, **kwargs):
        kwargs["class"] = "form-control"
        kwargs["placeholder"] = field.name
        return super(TextInput, self).__call__(field, **kwargs)


class PasswordInput(widgets.PasswordInput):
    def __call__(self, field, **kwargs):
        kwargs["class"] = "form-control"
        kwargs["placeholder"] = field.name
        return super(PasswordInput, self).__call__(field, **kwargs)


class LoginForm(Form):
    # email = TextField("Email", [validators.Required(), validators.Email()])
    email = TextField(
        "Email",
        [validators.Required(), validators.Email()],
        widget=TextInput(),
    )
    password = PasswordField(
        "Password",
        [validators.Required()],
        widget=PasswordInput(),
    )


class UserForm(Form):  # RENAME WHEN LOCATION COLUMN AND FORM ADDED?
    avatar_url = TextField(
        "Avatar",
        widget=TextInput(),
    )

# class LocationForm(form):  # IMPLIMENT THIS FORM WHEN LOCATION COLUMN ADDED
#     location = TextField(
#         "Location",
#         widget=TextInput(),
#     )


class NewUserForm(Form):
    username = TextField(
        "Username",
        [validators.Required()],
        widget=TextInput(),
    )
    email = TextField(
        "Email",
        [validators.Required(), validators.Email()],
        widget=TextInput(),
    )
    password = PasswordField(
        "Password",
        [validators.Required()],
        widget=PasswordInput(),
    )
