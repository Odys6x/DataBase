import os
from glob import glob
from sqlite3 import Error
import mysql
from flask import Flask, render_template, redirect, url_for, flash, session, request
from werkzeug.utils import secure_filename
from wtforms import TextAreaField, IntegerField, SubmitField, validators
import json
from flask_wtf import CSRFProtect, FlaskForm

from bookform import BookForm
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
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', [validators.NumberRange(min=1, max=5)])
    content = TextAreaField('Comment', [validators.DataRequired()])
    submit = SubmitField('Submit Revi   ew')


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
    insert_query = """
    INSERT IGNORE INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    # Initialize an empty list to store combined results
    combined_data = []

    try:
        # Get all JSON files from the directory
        json_files = glob('json/audio/*.json')

        # Loop through all files and combine their 'results' into one list
        for json_file in json_files:
            with open(json_file) as file:
                data = json.load(file)
                if 'results' in data:
                    combined_data.extend(data['results'])

        # Now, combined_data holds all 'results' from all the JSON files
        connection = create_connection()
        if connection is None:
            raise Exception("Failed to establish a database connection.")

        # Create necessary tables if they don't exist
        execute_query(connection, create_book_table)
        execute_query(connection, create_booklist_table)

        with connection.cursor() as cursor:
            # Insert data and ignore duplicates by title
            for book in combined_data:
                title = book.get('title', '').replace('[electronic resource]', '').strip()
                types = ', '.join(book.get('types', []))
                authors = ', '.join(book.get('authors', []))  # Handle missing authors
                abstract = ', '.join(book.get('abstracts', []))  # Handle missing abstracts
                languages = ', '.join(book.get('languages', []))  # Handle missing languages
                coverURL = book.get('coverUrl', '')
                subjects = book.get('subjects', '')
                isbns = ', '.join(book.get('isbns', []))  # Handle missing ISBNs
                createdDate = book.get('createdDate')

                if createdDate:
                    createdDate = datetime.strptime(createdDate, "%Y-%m-%d").date()
                else:
                    createdDate = None

                data_tuple = (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
                cursor.execute(insert_query, data_tuple)

            connection.commit()

        # Fetch the books from the database to pass to the template
        fetch_query = """
        SELECT id, title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns FROM Book;
        """
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
    return render_template("admin_index.html", books=books)


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    user_id = session.get('user_id')  # Get current logged-in user ID
    connection = create_connection()

    if connection is None:
        return "Database connection failed", 500  # Handle connection error
    if connection is not None:
        execute_query(connection, create_review_table)
        execute_query(connection, "CREATE INDEX idx_userId ON Review(userId);")
        execute_query(connection, "CREATE INDEX idx_bookId ON Review(bookId);")

    # Query to fetch book details (removed the Author table)
    query = """
        SELECT Book.id, Book.title, Book.abstract, Book.languages, Book.createdDate, Book.coverURL, 
               COUNT(Review.reviewId) as review_count, AVG(Review.ratings) as avg_rating
        FROM Book
        LEFT JOIN Review ON Book.id = Review.bookId
        WHERE Book.id = %s
        GROUP BY Book.id
    """

    # Query to fetch reviews (removed references to Author)
    reviews_query = """
    SELECT Book.id, Book.title, Book.abstract, Book.languages, 
           Review.content as review_content, Review.ratings, User.first_name, User.last_name
    FROM Book
    LEFT JOIN Review ON Book.id = Review.bookId
    LEFT JOIN User ON Review.userId = User.userId
    WHERE Book.id = %s
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
        'id': book[0],  # Book.id
        'title': book[1],  # Book.title
        'abstract': book[2],  # Book.abstract
        'languages': book[3],  # Book.languages
        'published_date': book[4],  # Book.createdDate
        'coverURL': book[5],  # Book.coverURL
        'review_count': book[6],  # Review count
        'avg_rating': round(book[7], 1) if book[7] is not None else None,
        'is_borrowed_by_user': is_borrowed_by_user,
        'is_borrowed_by_anyone': is_borrowed_by_anyone
    }

    return render_template("book.html", book=book_dict, form=form, reviews=reviews)



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
    WHERE email = %s;
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
        VALUES (%s, %s, %s, %s);
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
        WHERE book_id = %s AND user_id = %s AND is_returned = FALSE;
    """
    return_date = datetime.now().date()
    cursor = connection.cursor()
    cursor.execute(return_query, (return_date, book_id, user_id))
    connection.commit()

    cursor.close()
    connection.close()

    flash('You have successfully returned the book!', 'success')
    return redirect(url_for('user_history'))


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = BookForm()

    if form.validate_on_submit():
        # Extract the data from the form fields
        title = form.title.data or None
        types = form.types.data or None
        authors = form.authors.data or None
        abstract = form.abstract.data or None
        languages = form.languages.data or None
        created_date = form.createdDate.data or None
        cover_image_path = None
        print("Title field value:", form.title.data)
        print("Types field value:", form.types.data)
        print("Authors field value:", form.authors.data)
        print("Abstract field value:", form.abstract.data)
        print("Languages field value:", form.languages.data)
        print("Created Date field value:", form.createdDate.data)
        print("Cover Image File:", form.cover_image_file.data)
        print("Cover Image URL:", form.cover_image_url.data)
        print("Subjects field value:", form.subjects.data)
        print("ISBNs field value:", form.isbns.data)
        # Debug print statement to check form data

        print(f"Extracted Form Data: Title={title}, Types={types}, Authors={authors}, Abstract={abstract}, Languages={languages}, Created Date={created_date}")

        # Ensure the upload directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            print(f"Created directory: {app.config['UPLOAD_FOLDER']}")

        # Handle file upload if it exists
        if form.cover_image_file.data:
            filename = secure_filename(form.cover_image_file.data.filename)
            image_path = os.path.join('uploads', filename).replace('\\', '/')
            form.cover_image_file.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_image_path = image_path  # Use the file path as the cover image path
            print(f"File uploaded successfully and saved at: {cover_image_path}")

        # If no file was uploaded, check for a URL
        elif form.cover_image_url.data:
            cover_image_path = form.cover_image_url.data  # Use the URL as the cover image
            print(f"Using Cover Image URL: {cover_image_path}")

        subjects = form.subjects.data or None
        isbns = form.isbns.data or None

        # Debug print statement to check the complete book data
        print(f"Final Book Data to be added: {title}, {types}, {authors}, {abstract}, {languages}, {created_date}, {cover_image_path}, {subjects}, {isbns}")

        # Create the book_data tuple with all the extracted data
        book_data = (title, types, authors, abstract, languages, created_date, cover_image_path, subjects, isbns)

        try:
            connection = create_connection()
            if connection is not None:
                with connection.cursor() as cursor:
                    insert_query = """
                    INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    cursor.execute(insert_query, book_data)
                    connection.commit()
                    flash('Book added successfully!', 'success')
                    print("Book successfully added to the database.")
                return redirect(url_for('admin_index'))
            else:
                flash('Database connection failed.', 'danger')
                print("Database connection failed.")
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            print(f"SQL Error: {err}")  # Print specific SQL error for debugging
        finally:
            if connection is not None:
                connection.close()

    else:
        # Print form errors to debug validation issues
        print("Form validation failed with errors:", form.errors)

    return render_template('add_book.html', form=form)


@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    # SQL query to delete the book by ID
    delete_query = "DELETE FROM Book WHERE id = %s;"

    print(f"Book ID to delete: {book_id}")  # Debugging

    try:
        # Create the database connection
        connection = create_connection()
        if connection is not None:
            with connection.cursor() as cursor:
                # Execute the delete query
                cursor.execute(delete_query, (book_id,))
                # Check if any rows were affected (i.e., the book was deleted)
                if cursor.rowcount > 0:
                    connection.commit()
                    flash('Book deleted successfully!', 'success')
                else:
                    flash(f"No book found with ID {book_id}.", 'warning')
        else:
            flash('Failed to connect to the database.', 'danger')

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        print(f"Error: {err}")  # Log the error for debugging

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for('admin_index'))


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    connection = create_connection()
    if connection is None:
        flash("Database connection failed.", "danger")
        return redirect(url_for('admin_index'))

    # Fetch the book details from the database
    query = "SELECT * FROM Book WHERE id = %s"
    with connection.cursor(dictionary=True) as cursor:  # Fetching as a dictionary to use in the form
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for('admin_index'))

    # Convert the date to a datetime object if it is not None
    if 'createdDate' in book and book['createdDate']:
        if isinstance(book['createdDate'], str):
            try:
                book['createdDate'] = datetime.strptime(book['createdDate'], '%Y-%m-%d').date()
            except ValueError:
                book['createdDate'] = None  # Set to None if the format is invalid

    print("Book data being passed to the form:", book)

    form = BookForm(data=book)

    # Ensure the existing cover URL is set properly for the form
    if book['coverURL']:
        # Prepend 'static/' to coverURL if it's stored without it in the database
        book['coverURL'] = f"static/{book['coverURL']}" if not book['coverURL'].startswith('http') else book['coverURL']

    # Convert the date input to the correct format before updating the database
    if form.validate_on_submit():
        # Handle empty values for all fields, setting them to None if they are empty
        title = form.title.data or None
        types = form.types.data or None
        authors = form.authors.data or None
        abstract = form.abstract.data or None
        languages = form.languages.data or None
        created_date = form.createdDate.data or None

        # Handle the cover URL and image file correctly
        cover_url = form.cover_image_url.data or book['coverURL']  # Pre-fill the URL with existing image if not edited
        # Ensure the upload directory exists
        if form.cover_image_file.data:
            filename = secure_filename(form.cover_image_file.data.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\', '/')

            # Ensure that the image path does not contain multiple 'static/' parts
            if image_path.startswith('static/'):
                image_path = image_path.replace('static/', '', 1)

            form.cover_image_file.data.save(os.path.join('static', image_path))
            cover_url = image_path  # Use the corrected file path

        subjects = form.subjects.data or None
        isbns = form.isbns.data or None

        # Update the book details in the database
        update_query = """
        UPDATE Book SET title = %s, types = %s, authors = %s, abstract = %s, languages = %s, createdDate = %s, coverURL = %s, subjects = %s, isbns = %s WHERE id = %s;
        """
        updated_book_data = (
            title,
            types,
            authors,
            abstract,
            languages,
            created_date,
            cover_url,
            subjects,
            isbns,
            book_id
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(update_query, updated_book_data)
                connection.commit()
                flash('Book updated successfully!', 'success')
            return redirect(url_for('adminbook_detail', book_id=book_id))

        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")

        finally:
            connection.close()

    # Render the edit form with the current book data
    return render_template('edit_book.html', form=form, book_id=book_id, book=book)

@app.route('/adminbook/<int:book_id>')
def adminbook_detail(book_id):
    connection = create_connection()
    if connection is None:
        return "Database connection failed", 500  # Handle connection error

    query = "SELECT id, title, authors, types, abstract, languages, createdDate, coverURL, subjects, isbns FROM Book WHERE id = %s"
    cursor = connection.cursor()

    try:
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()  # Fetch a single result
    except Error as e:
        print(f"The error '{e}' occurred")
        return "An error occurred while fetching the book", 500
    finally:
        cursor.close()
        connection.close()  # Always close the connection

    if book is None:
        return "Book not found", 404

    # Convert the result to a dictionary for easy access in the template
    book_dict = {
        'id': book[0],  # Assuming book.id is at index 0
        'title': book[1],  # Assuming book.title is at index 1
        'authors': book[2],  # Assuming book.authors is at index 2
        'types': book[3],  # Assuming book.types is at index 3
        'abstract': book[4],  # Assuming book.abstract is at index 4
        'languages': book[5],  # Assuming book.languages is at index 5
        'createdDate': book[6],  # Assuming book.createdDate is at index 6
        'coverURL': book[7],  # Assuming book.coverURL is at index 7
        'subjects': book[8],  # Assuming book.subjects is at index 8
        'isbns': book[9]  # Assuming book.isbns is at index 9
    }

    return render_template("adminbook_details.html", book=book_dict)

@app.route('/search', methods=['GET'])
def search_books():
    search_query = request.args.get('search', '')  # Get the search term from the query string

    if not search_query:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('index'))

    connection = create_connection()

    # SQL query to search for books by title
    search_sql = "SELECT id, title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns FROM Book WHERE title LIKE %s"
    cursor = connection.cursor(dictionary=True)
    search_term = f"%{search_query}%"
    cursor.execute(search_sql, (search_term,))
    books = cursor.fetchall()

    cursor.close()
    connection.close()

    if not books:
        flash(f'No books found for "{search_query}".', 'info')
        return redirect(url_for('index'))

    return render_template('index.html', books=books, search_query=search_query)

if __name__ == "__main__":
    create_admin_user()
    app.run(debug=True)