from datetime import datetime

import mysql
from flask import Flask, render_template
import json
from conn import create_connection, execute_query
from query import create_table

app = Flask(__name__)


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
        execute_query(connection, create_table_query)

        # Check if the table is empty before inserting new data
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Book;")
            count = cursor.fetchone()[0]

            if count == 0:  # Only insert if the table is empty
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
