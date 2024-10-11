# bookForm.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, SelectField
from wtforms.validators import Optional, DataRequired
from wtforms import StringField
from wtforms.validators import Optional, URL
from flask_wtf.file import FileAllowed
from flask_wtf.file import FileField, FileAllowed


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(message="Title is required")])
    types = SelectField('Book Type', choices=[('Audio Book', 'Audio Book'), ('E Book', 'E Book')], validators=[Optional()])
    authors = StringField('Authors', validators=[Optional()])
    abstract = TextAreaField('Abstract', validators=[Optional()])
    languages = StringField('Languages', validators=[Optional()])
    createdDate = DateField('Created Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    cover_image_file = FileField('Upload Cover Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    cover_image_url = StringField('Cover Image URL', validators=[Optional(), URL(message="Invalid URL format")])
    subjects = StringField('Subjects', validators=[Optional()])
    isbns = StringField('ISBNs', validators=[Optional()])
    submit = SubmitField('Add Book')
