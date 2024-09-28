from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import re  # Regular expression module

# Custom email validation
def email_check(form, field):
    email = field.data
    # Regular expression for validating an Email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        raise ValidationError("Invalid email format.")

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), email_check])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
