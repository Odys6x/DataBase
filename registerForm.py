from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
import re  # Regular expression module

# Custom validator to check password strength
def password_check(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least one digit.")

# Custom email validation
def email_check(form, field):
    email = field.data
    # Regular expression for validating an Email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        raise ValidationError("Invalid email format.")

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(max=50)])  # Not required
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), email_check])  # Added email_check
    password = PasswordField('Password', validators=[DataRequired(), password_check])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    agree = BooleanField('Agree to terms and conditions', validators=[DataRequired()])
    submit = SubmitField('Register')
