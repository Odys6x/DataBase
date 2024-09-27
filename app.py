from datetime import datetime
import mysql
from flask import Flask, render_template, redirect, url_for, flash
import json
from flask_wtf import CSRFProtect
from conn import create_connection, execute_query
from query import create_user_table
from werkzeug.security import generate_password_hash
from registerForm import RegistrationForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inf2003_database'  # Change this to a secure key
csrf = CSRFProtect(app)

def create_admin_user():
    create_user_query = create_user_table
    create_admin_query = """
    INSERT INTO User (first_name, last_name, email, password, fees_due, user_type)
    VALUES ('Admin', '1', 'admin@email.com', 'admin1234', 0.00, 'a');
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
                    cursor.execute(create_admin_query)
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
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    create_user_query = create_user_table
    form = RegistrationForm()

    if form.validate_on_submit():  # Validate form submission
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        # Hash the password and truncate to 29 characters
        hashed_password = generate_password_hash(password)[:29]

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
if __name__ == "__main__":
    create_admin_user()
    app.run(debug=True)
