# bookForm.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, SelectField
from wtforms.validators import Optional, DataRequired
from wtforms import StringField
from wtforms.validators import Optional, URL
from flask_wtf.file import FileAllowed
from flask_wtf.file import FileField, FileAllowed


class BookForm(FlaskForm):
    title = StringField('Title', [DataRequired()])
    types = StringField('Types', [Optional()])
    authors = StringField('Authors', [Optional()])
    abstract = TextAreaField('Abstract', [Optional()])
    languages = StringField('Languages', [Optional()])
    createdDate = DateField('Created Date', format='%Y-%m-%d', validators=[Optional()])
    cover_image_file = FileField('Cover Image File', validators=[Optional(),FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    cover_image_url = StringField('Cover Image URL', [Optional(), URL(message="Invalid URL")])
    subjects = StringField('Subjects', [Optional()])
    isbns = StringField('ISBNs', [Optional()])
    submit = SubmitField('Submit')

