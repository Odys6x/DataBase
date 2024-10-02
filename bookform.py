# bookForm.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    types = SelectField('Book Type', choices=[('Audio Book', 'Audio Book'), ('E Book', 'E Book')], validators=[DataRequired()])
    authors = StringField('Authors', validators=[DataRequired()])
    abstract = TextAreaField('Abstract')
    languages = StringField('Languages')
    createdDate = DateField('Created Date (YYYY-MM-DD)', format='%Y-%m-%d')
    coverURL = StringField('Cover URL')
    subjects = StringField('Subjects')
    isbns = StringField('ISBNs')
    submit = SubmitField('Add Book')
