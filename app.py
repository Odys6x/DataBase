from datetime import datetime
from sqlite3 import Error

import mysql
from flask import Flask, render_template, redirect, url_for, flash, session
import json
from flask_wtf import CSRFProtect
from conn import create_connection, execute_query
from query import create_user_table, create_table
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from registerForm import RegistrationForm
from loginForm import LoginForm
from bookform import BookForm

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

    create_table_query = create_table

    insert_query = """
    INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    try:
        connection = create_connection()
        if connection is None:
            raise Exception("Failed to establish a database connection.")

        execute_query(connection, create_table_query)

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
    with open('json/audio/nlb_api_response0.json') as file:
        data = json.load(file)

    create_table_query = create_table

    insert_query = """
    INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    try:
        connection = create_connection()
        if connection is None:
            raise Exception("Failed to establish a database connection.")

        execute_query(connection, create_table_query)

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


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = BookForm()

    if form.validate_on_submit():
        title = form.title.data
        types = form.types.data
        authors = form.authors.data
        abstract = form.abstract.data
        languages = form.languages.data
        createdDate = form.createdDate.data
        coverURL = form.coverURL.data
        subjects = form.subjects.data
        isbns = form.isbns.data

        # SQL query to insert book details into the Book table
        insert_query = """
        INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        try:
            connection = create_connection()
            if connection is not None:
                with connection.cursor() as cursor:
                    cursor.execute(insert_query, (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns))
                    connection.commit()
                    flash('Book added successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Database connection failed.', 'danger')

        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')

        finally:
            if connection is not None:
                connection.close()

    return render_template('add_book.html', form=form)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    # SQL query to delete the book by ID
    delete_query = "DELETE FROM Book WHERE id = %s"
    
    try:
        connection = create_connection()
        if connection is not None:
            with connection.cursor() as cursor:
                cursor.execute(delete_query, (book_id,))
                connection.commit()
                flash('Book deleted successfully!', 'success')
        else:
            flash('Failed to connect to the database.', 'danger')

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')

    finally:
        if connection is not None:
            connection.close()

    return redirect(url_for('index'))

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    connection = create_connection()
    if connection is None:
        flash("Database connection failed.", "danger")
        return redirect(url_for('index'))

    # Fetch the book details from the database
    query = "SELECT * FROM Book WHERE id = %s"
    with connection.cursor(dictionary=True) as cursor:  # Fetching as a dictionary to use in the form
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for('index'))

    # Create an instance of the form with book data pre-filled
    form = BookForm(data=book)

    if form.validate_on_submit():
        # Update the book details in the database
        update_query = """
        UPDATE Book SET title = %s, types = %s, authors = %s, abstract = %s, languages = %s, createdDate = %s, coverURL = %s, subjects = %s, isbns = %s WHERE id = %s
        """
        updated_book_data = (
            form.title.data,
            form.types.data,
            form.authors.data,
            form.abstract.data,
            form.languages.data,
            form.createdDate.data,
            form.coverURL.data,
            form.subjects.data,
            form.isbns.data,
            book_id
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(update_query, updated_book_data)
                connection.commit()
                flash('Book updated successfully!', 'success')
            return redirect(url_for('book_detail', book_id=book_id))

        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")

        finally:
            connection.close()

    # Render the edit form with the current book data
    return render_template('edit_book.html', form=form, book_id=book_id)


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    connection = create_connection()
    if connection is None:
        return "Database connection failed", 500  # Handle connection error

    query = f'SELECT * FROM book WHERE id = {book_id}'
    cursor = connection.cursor()

    try:
        cursor.execute(query)
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
        'author': book[3],  # Assuming book.author is at index 2
        'coverURL': book[7],  # Assuming book.coverURL is at index 3
        'description': book[4],  # Assuming book.description is at index 4
        'published_date': book[6],  # Assuming book.published_date is at index 5
    }

    return render_template("book.html", book=book_dict)



if __name__ == "__main__":
    create_admin_user()
    app.run(debug=True)
