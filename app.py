from sqlite3 import Error
import mysql
from flask import Flask, render_template, redirect, url_for, flash, session, request
from wtforms import TextAreaField, IntegerField, SubmitField, validators
import json
from flask_wtf import CSRFProtect, FlaskForm
from conn import create_connection, execute_query
from query import create_user_table, create_book_table, create_booklist_table, create_review_table
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from registerForm import RegistrationForm
from loginForm import LoginForm
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inf2003_database'  # Change this to a secure key
csrf = CSRFProtect(app)

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', [validators.NumberRange(min=1, max=5)])
    content = TextAreaField('Comment', [validators.DataRequired()])
    submit = SubmitField('Submit Review')


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
            ratings = int(request.form['ratings'])  # ensure integer value
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

@app.route('/')
def index():
    with open('json/audio/nlb_api_response0.json') as file:
        data = json.load(file)



    insert_query = """
    INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    try:
        connection = create_connection()
        if connection is None:
            raise Exception("Failed to establish a database connection.")

        execute_query(connection, create_book_table)
        execute_query(connection, create_booklist_table)

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
        query = "SELECT userId, email, password, user_type FROM User WHERE email = %s"
        connection = None

        try:
            connection = create_connection()
            if connection is not None:  # Check if connection is valid
                with connection.cursor() as cursor:
                    cursor.execute(query, (email,))
                    user = cursor.fetchone()

                    if user and check_password_hash(user[2], password):  # Verify password
                        # Set session variables
                        session['user_id'] = user[0]
                        session['email'] = user[1]
                        session['user_type'] = user[3]

                        flash('Login successful!', 'success')

                        # Redirect based on user type
                        if user[3] == 'a':  # Admin
                            return redirect(url_for('admin_index'))
                        elif user[3] == 'u':  # Regular user
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


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    user_id = session.get('user_id')  # Get current logged-in user ID
    connection = create_connection()

    if connection is None:
        return "Database connection failed", 500  # Handle connection error
    if connection is not None:
        execute_query(connection, create_review_table)

    # Query to fetch book details
    query = "SELECT * FROM book WHERE id = %s"
    reviews_query = """
    SELECT Review.ratings, Review.content, User.first_name, User.last_name 
    FROM Review 
    JOIN User ON Review.userId = User.userId 
    WHERE Review.bookId = %s
    """
    cursor = connection.cursor()

    try:
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()  # Fetch the book details

        # Check if the book is borrowed by the current user
        check_borrow_query = """
        SELECT * FROM BorrowedList WHERE book_id = %s AND user_id = %s AND is_returned = FALSE
        """
        cursor.execute(check_borrow_query, (book_id, user_id))
        is_borrowed_by_user = cursor.fetchone() is not None  # True if the current user borrowed the book

        # Check if the book is borrowed by any user (other than the current one)
        check_any_borrow_query = """
        SELECT * FROM BorrowedList WHERE book_id = %s AND is_returned = FALSE
        """

        form = ReviewForm()
        cursor.execute(reviews_query, (book_id,))
        reviews = cursor.fetchall()

        cursor.execute(check_any_borrow_query, (book_id,))
        is_borrowed_by_anyone = cursor.fetchone() is not None  # True if the book is currently borrowed by anyone

    except Error as e:
        print(f"The error '{e}' occurred")
        return "An error occurred while fetching the book", 500

    finally:
        cursor.close()
        connection.close()

    if book is None:
        return "Book not found", 404

    # Convert the result to a dictionary for easy access in the template
    book_dict = {
        'id': book[0],  # Assuming book.id is at index 0
        'title': book[1],  # Assuming book.title is at index 1
        'author': book[3],  # Assuming book.author is at index 2
        'coverURL': book[7],  # Assuming book.coverURL is at index 3
        'description': book[4],  # Assuming book.description is at index 4
        'published_date': book[6],  # Assuming book.published_date is at index 5
        'is_borrowed_by_user': is_borrowed_by_user,  # True if the current user borrowed the book
        'is_borrowed_by_anyone': is_borrowed_by_anyone  # True if the book is borrowed by anyone
    }
    print(reviews)

    return render_template("book.html", book=book_dict, form=form,reviews=reviews)


@app.route('/history')
def user_history():
    #user_id = 1  # Temporarily hardcoding a user ID for testing
    user_id = session['user_id']
    connection = create_connection()

    history_query = """
        SELECT b.title, bl.borrow_date, bl.due_date, bl.return_date, bl.is_returned
        FROM BorrowedList bl
        JOIN Book b ON bl.book_id = b.id
        WHERE bl.user_id = %s
    """
    cursor = connection.cursor(dictionary=True)
    cursor.execute(history_query, (user_id,))
    borrow_history = cursor.fetchall()

    # Calculate overdue days and fees
    current_date = datetime.now().date()
    for record in borrow_history:
        if not record['is_returned'] and record['due_date']:
            overdue_days = (current_date - record['due_date']).days
            record['overdue_days'] = max(0, overdue_days)  # If overdue, calculate days
            record['overdue_fees'] = record['overdue_days'] * 1  # $1 per day overdue
        else:
            record['overdue_days'] = 0
            record['overdue_fees'] = 0

    cursor.close()
    connection.close()

    return render_template('history.html', borrow_history=borrow_history)

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

@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    #user_id = 1  # Temporarily hardcoding a user ID for testing without login
    user_id = session['user_id']
    print(user_id)
    connection = create_connection()

    # Check if the book is already borrowed
    check_query = "SELECT * FROM BorrowedList WHERE book_id = %s AND is_returned = FALSE"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(check_query, (book_id,))
    book_borrowed = cursor.fetchone()

    if book_borrowed:
        flash('Book is currently borrowed by someone else.', 'danger')
        return redirect(url_for('book_detail', book_id=book_id))

    # If book is not borrowed, allow user to borrow
    borrow_date = datetime.now().date()
    due_date = borrow_date + timedelta(days=14)  # 2-week borrowing period

    borrow_query = """
        INSERT INTO BorrowedList (user_id, book_id, borrow_date, due_date)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(borrow_query, (user_id, book_id, borrow_date, due_date))
    connection.commit()

    cursor.close()
    connection.close()

    flash('You have successfully borrowed the book!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    # user_id = 1  # Temporarily hardcoding a user ID for testing without login
    user_id = session['user_id']
    connection = create_connection()

    return_query = """
        UPDATE BorrowedList
        SET return_date = %s, is_returned = TRUE
        WHERE book_id = %s AND user_id = %s AND is_returned = FALSE
    """
    return_date = datetime.now().date()
    cursor = connection.cursor()
    cursor.execute(return_query, (return_date, book_id, user_id))
    connection.commit()

    cursor.close()
    connection.close()

    flash('You have successfully returned the book!', 'success')
    return redirect(url_for('user_history'))

if __name__ == "__main__":
    create_admin_user()
    app.run(debug=True)