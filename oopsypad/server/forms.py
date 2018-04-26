from flask_security.forms import (RegisterForm,
                                  email_required, email_validator,
                                  password_length, password_required, unique_user_email)
from wtforms import PasswordField, StringField, SubmitField


class AdminRegisterForm(RegisterForm):
    email = StringField('Admin Email', validators=[email_required,
                                                   email_validator,
                                                   unique_user_email])
    password = PasswordField('Admin Password', validators=[password_required,
                                                           password_length])
    submit = SubmitField()
