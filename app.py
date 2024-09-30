from datetime import datetime
from sqlite3 import Error

import mysql
from flask import Flask, render_template, redirect, url_for, flash, session, request
import json
from flask_wtf import CSRFProtect, FlaskForm
from flask_wtf.csrf import generate_csrf
from wtforms import TextAreaField, IntegerField, SubmitField, validators
from conn import create_connection, execute_query
from query import create_user_table, create_book_table, create_review_table
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from registerForm import RegistrationForm
from loginForm import LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inf2003_database'  # Change this to a secure key
csrf = CSRFProtect(app)

def create_admin_user():
    create_user_query = create_user_table

    # Hash the admin password before insertion
    admin_password = generate_password_hash('admin1234')  # Hash the password

    create_admin_query = """
    INSERT INTO User (first_name, last_name, email, password, fees_due, user_type)
    VALUES (%s, %s, %s, %s, %s, %s);
    """

    check_admin_query = "SELECT COUNT(*) FROM User WHERE user_type = 'a';"

    try:
        connection = create_connection()
        if connection is not None:  # Check if the connection was successful
            execute_query(connection, create_user_query)
            with connection.cursor() as cursor:
                # Check if an admin already exists
                cursor.execute(check_admin_query)
                admin_count = cursor.fetchone()[0]

                if admin_count == 0:  # If no admin exists, create one
                    cursor.execute(create_admin_query, ('Admin', '1', 'admin@email.com', admin_password, 0.00, 'a'))
                    connection.commit()
                    print("Admin user created successfully.")
                else:
                    print("Admin user already exists.")
        else:
            print("Failed to create database connection.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if connection is not None:
            connection.close()


@app.route('/')
def index():
    with open('json/audio/nlb_api_response0.json') as file:
        data = json.load(file)

    create_book_table_query = create_book_table

    insert_query = """
    INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    try:
        connection = create_connection()
        if connection is None:
            raise Exception("Failed to establish a database connection.")

        execute_query(connection, create_book_table_query)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Book;")
            count = cursor.fetchone()[0]

            if count == 0:
                for book in data['results']:
                    title = book['title'].replace('[electronic resource]', '').strip()
                    types = ', '.join(book['types'])
                    authors = ', '.join(book['authors'])
                    abstract = ', '.join(book['abstracts'])
                    languages = ', '.join(book['languages'])
                    coverURL = book.get('coverUrl', '')
                    subjects = book.get('subjects', '')
                    isbns = ', '.join(book['isbns'])
                    createdDate = book.get('createdDate')

                    if createdDate:
                        createdDate = datetime.strptime(createdDate, "%Y-%m-%d").date()
                    else:
                        createdDate = None

                    data_tuple = (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
                    cursor.execute(insert_query, data_tuple)

                connection.commit()

        fetch_query = "SELECT id, title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns FROM Book;"
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(fetch_query)
            books = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        books = []

    except Exception as e:
        print(f"An error occurred: {e}")
        books = []

    finally:
        if connection:
            connection.close()

    # Pass the books data to the template
    return render_template("index.html", books=books)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():  # When the form is submitted
        email = form.email.data
        password = form.password.data

        # SQL query to find user by email
        query = "SELECT email, password, user_type FROM User WHERE email = %s"
        connection = None

        try:
            connection = create_connection()
            if connection is not None:  # Check if connection is valid
                with connection.cursor() as cursor:
                    cursor.execute(query, (email,))
                    user = cursor.fetchone()

                    if user and check_password_hash(user[1], password):  # Verify password
                        # Set session variables
                        session['email'] = user[0]
                        session['user_type'] = user[2]

                        flash('Login successful!', 'success')

                        # Redirect based on user type
                        if user[2] == 'a':  # Admin
                            return redirect(url_for('admin_index'))
                        elif user[2] == 'u':  # Regular user
                            return redirect(url_for('index'))
                    else:
                        flash('Login failed. Check your email and password.', 'danger')
            else:
                flash("Error: Could not establish a connection to the database.", 'danger')

        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')

        finally:
            if connection is not None:
                connection.close()

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    create_user_query = create_user_table
    form = RegistrationForm()

    if form.validate_on_submit():  # Validate form submission
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        hashed_password = generate_password_hash(password)

        # Define user type
        user_type = 'u'  # For regular users

        # SQL query to insert data into the User table
        insert_query = """
        INSERT INTO User (first_name, last_name, email, password, user_type)
        VALUES (%s, %s, %s, %s, %s);
        """

        # Create a tuple with form values, including user_type
        user_data = (first_name, last_name, email, hashed_password, user_type)

        connection = None  # Initialize connection variable
        try:
            # Establish a connection and execute the query
            connection = create_connection()
            if connection is not None:  # Check if connection is valid
                execute_query(connection, create_user_query)
                with connection.cursor() as cursor:
                    cursor.execute(insert_query, user_data)
                    connection.commit()

                flash('Registration successful!', 'success')
                return redirect(url_for('login'))
            else:
                flash("Error: Could not establish a connection to the database.", 'danger')
                return redirect(url_for('register'))

        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            return redirect(url_for('register'))

        finally:
            if connection is not None:
                connection.close()

    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    # Clear the user session
    session.clear()  # This logs out the user by clearing their session data
    flash('You have been logged out.', 'info')  # Display a message
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/admin_index')
def admin_index():
    return render_template("admin_index.html")

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', [validators.NumberRange(min=1, max=5)])
    content = TextAreaField('Comment', [validators.DataRequired()])
    submit = SubmitField('Submit Review')

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    create_reviews_query = create_review_table

    connection = create_connection()
    if connection is None:
        return "Database connection failed", 500  # Handle connection error
    
    # Create the review table if it doesn't exist
    if connection is not None:  
        execute_query(connection, create_reviews_query)

    book_query = 'SELECT * FROM Book WHERE id = %s'

    reviews_query = """
    SELECT Review.ratings, Review.content, User.first_name, User.last_name 
    FROM Review 
    JOIN User ON Review.userId = User.userId 
    WHERE Review.bookId = %s
    """

    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch the book details
            cursor.execute(book_query, (book_id,))
            book = cursor.fetchone()  # This will return None if no book is found

            # If no book is found, return a 404 page
            if not book:
                flash('Book not found.', 'danger')
                return redirect(url_for('index'))
            
            # Create a form instance
            form = ReviewForm()

            # Fetch all reviews for the book
            cursor.execute(reviews_query, (book_id,))
            reviews = cursor.fetchall()

            # Convert the result to a dictionary for easy access in the template
            book_dict = {
                'id': book['id'],  # Fetch by column name
                'title': book['title'],  # Fetch by column name
                'author': book['authors'],  # Fetch by column name
                'coverURL': book['coverURL'],  # Fetch by column name
                'description': book['abstract'],  # Fetch by column name
                'published_date': book['createdDate'],  # Fetch by column name
            }

            return render_template("book.html", book=book_dict, form=form, reviews=reviews)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred while fetching the book", 500
    finally:
        connection.close()


# Submit review handling
@app.route('/book/<int:book_id>/submit_review', methods=['POST'])
def submit_review(book_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    # Get the logged-in user's email from the session
    email = session['email']

    # Fetch the userId based on the email
    connection = create_connection()
    user_query = "SELECT userId FROM User WHERE email = %s"
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(user_query, (email,))
            user = cursor.fetchone()
            if user is None:
                flash('User not found', 'danger')
                return redirect(url_for('login'))

            user_id = user[0]  # Extract userId from the query result
            
            # Get form data for the review
            ratings = int(request.form['ratings']) # ensure integer value
            content = request.form['content']

            # Insert the review into the database
            review_insert_query = """
            INSERT INTO Review (userId, bookId, content, ratings) 
            VALUES (%s, %s, %s, %s);
            """
            cursor.execute(review_insert_query, (user_id, book_id, content, ratings))
            connection.commit()
            print(f"Review successfully inserted for user {user_id} on book {book_id}.")

            flash('Review submitted successfully!', 'success')
            return redirect(url_for('book_detail', book_id=book_id))        

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        print(f"Error inserting review: {err}")
        return redirect(url_for('book_detail', book_id=book_id))
    finally:
        if connection:
            connection.close()


@app.route('/account')
def account():
    if 'email' not in session:
        flash('You need to log in to access your account.', 'danger')
        return redirect(url_for('login'))

    email = session['email']

    connection = create_connection()
    query = "SELECT first_name, last_name, email FROM User WHERE email = %s"

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if not user:
                flash('User not found.', 'danger')
                return redirect(url_for('login'))

        # Pass the user object and csrf token to the template
        return render_template('account.html', user=user)

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return redirect(url_for('index'))

    finally:
        if connection:
            connection.close()

@app.route('/updateProfile', methods=['POST'])
def update_profile():
    if 'email' not in session:
        flash('You need to log in to update your profile.', 'danger')
        return redirect(url_for('login'))

    email = session['email']
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    new_email = request.form['email']

    # Update the user's information in the database
    connection = create_connection()
    update_query = """
    UPDATE User
    SET first_name = %s, last_name = %s, email = %s
    WHERE email = %s
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(update_query, (first_name, last_name, new_email, email))
            connection.commit()

            # Update the session with the new email if it has been changed
            if email != new_email:
                session['email'] = new_email

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('account'))

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return redirect(url_for('account'))

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    create_admin_user()
    app.run(debug=True)
