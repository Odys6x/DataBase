from datetime import datetime

import mysql
from flask import Flask, render_template
import json
from conn import create_connection, execute_query

app = Flask(__name__)


@app.route('/')
def index():
    # Load the JSON data from file
    with open('json/audio/nlb_api_response0.json') as file:
        data = json.load(file)

    # Create the table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Book (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(500) NOT NULL,
        types VARCHAR(100),  -- Increased size to avoid truncation
        authors VARCHAR(500),
        abstract LONGTEXT,
        languages TEXT,
        createdDate DATE,
        coverURL VARCHAR(5000),
        subjects VARCHAR(200),
        isbns VARCHAR(1000)
    );
    """

    insert_query = """
    INSERT INTO Book (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    try:
        connection = create_connection()

        # Execute the table creation query
        execute_query(connection, create_table_query)

        # Insert data from JSON into the database
        with connection.cursor() as cursor:
            for book in data['results']:
                title = book['title']
                types = ', '.join(book['types'])
                authors = ', '.join(book['authors'])
                abstract = ', '.join(book['abstracts'])
                languages = ', '.join(book['languages'])
                coverURL = book.get('coverUrl', '')
                subjects = book.get('subjects', '')
                isbns = ', '.join(book['isbns'])
                createdDate = book.get('createdDate')

                # Parse the createdDate if it exists
                if createdDate:
                    createdDate = datetime.strptime(createdDate, "%Y-%m-%d").date()
                else:
                    createdDate = None

                # Data tuple for insertion
                data_tuple = (title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns)
                cursor.execute(insert_query, data_tuple)

            # Commit all inserts
            connection.commit()

        # Fetch the data from the database to display it
        fetch_query = "SELECT title, types, authors, abstract, languages, createdDate, coverURL, subjects, isbns FROM Book;"
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(fetch_query)
            books = cursor.fetchall()  # Fetch all rows

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        books = []

    finally:
        connection.close()

    # Pass the books data to the template
    return render_template("index.html", books=books)


@app.route('/login')
def login():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
