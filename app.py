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
import pandas as pd
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

def insert_pbooks():
    # Read the CSV file
    df = pd.read_csv('BooksDataset.csv')
    df.drop_duplicates(subset=['Title'], inplace=True)
    df.dropna(subset=['Description'], inplace=True)
    # Rename columns to match SQL table
    df.rename(columns={
        'Title': 'title',
        'Authors': 'authors',
        'Description': 'abstract',
        'Category': 'subjects'
    }, inplace=True)

    # Add new columns
    df['types'] = 'Physical Book'
    df['coverURL'] = 'image/default.png'

    # Convert and format 'Publish Date'
    df['Publish Date'] = pd.to_datetime(df['Publish Date'], format="%A, %B %d, %Y", errors='coerce')
    df.dropna(subset=['Publish Date'], inplace=True)
    df['Publish Date'] = df['Publish Date'].dt.strftime('%Y-%m-%d')
    df.rename(columns={
        'Publish Date': 'createdDate'
    }, inplace=True)

    print(df)  # Optionally, print the DataFrame for verification
    create_table_query = create_table

    # Prepare the insert query
    insert_query = """
    INSERT IGNORE INTO book (title, types, authors, abstract, createdDate, coverURL, subjects)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """

    try:
        connection = create_connection()
        if connection is not None:  # Check if the connection was successful
            execute_query(connection, create_table_query)

            # Count existing books in the database
            count_query = "SELECT COUNT(*) FROM book;"
            with connection.cursor() as cursor:
                cursor.execute(count_query)
                count = cursor.fetchone()[0]
                print(f"Current book count: {count}")

                # Check if count exceeds 1000
                if count >= 1000:
                    print("Book count exceeds 1000. No new books will be inserted.")
                      # Exit the function if more than 1000 books exist
                else:
                # Insert new books
                 for index, row in df.iterrows():
                    cursor.execute(insert_query, (
                        row['title'],
                        row['types'],
                        row['authors'],
                        row['abstract'],
                        row['createdDate'],
                        row['coverURL'],
                        row['subjects']
                    ))
                connection.commit()
                print("Data inserted successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if connection is not None:
            connection.close()

@app.route('/')
def index():
    #with open('json/audio/nlb_api_response0.json') as file:
    with open('nlb_api_response0.json') as file:
        data = json.load(file)

    create_table_query = create_table

    insert_query = """
    INSERT INTO book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
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
    return render_template("admin_index.html")


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
    insert_pbooks()
    app.run(debug=True)
