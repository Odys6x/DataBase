import os
from bson import ObjectId
from flask import Flask, render_template, redirect, url_for, flash, session, request
from werkzeug.utils import secure_filename
from wtforms import TextAreaField, IntegerField, SubmitField, validators
import json
from flask_wtf import CSRFProtect, FlaskForm
from pymongo import MongoClient, ReturnDocument
from bookform import BookForm
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from registerForm import RegistrationForm
from loginForm import LoginForm
import pymongo
from datetime import datetime, timedelta
from threading import Lock
import contextlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inf2003_database'  # Change this to a secure key
csrf = CSRFProtect(app)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = MongoClient('mongodb+srv://Admin:newpassword@mydb.9hyfl.mongodb.net/')  # Connect to MongoDB
db = client['LibraryDB']  # Replace with your database name
books_collection = db['Book']  # Collection for books
users_collection = db['User']  # Collection for users
reviews_collection = db['Review']
borrow_collection = db['BorrowedList']
borrow_lock = Lock()

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', [validators.NumberRange(min=1, max=5)])
    content = TextAreaField('Comment', [validators.DataRequired()])
    submit = SubmitField('Submit Review')


def create_admin_user():
    admin_password = generate_password_hash('admin1234')  # Hash the password

    if users_collection.count_documents({'user_type': 'a'}) == 0:  # Check if an admin exists
        users_collection.insert_one({
            'first_name': 'Admin',
            'last_name': '1',
            'email': 'admin@email.com',
            'password': admin_password,
            'fees_due': 0.00,
            'user_type': 'a'
        })
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")


@contextlib.contextmanager
def safe_db_operation():
    try:
        yield
    except Exception as e:
        print(f"Database operation failed: {e}")
        raise


@app.route('/book/<string:book_id>/submit_review', methods=['POST'])
def submit_review(book_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    user = users_collection.find_one({'email': email})

    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

    user_id = user['userId']  # Extract userId from the query result

    # Get form data for the review
    ratings = int(request.form['rating'])  # ensure integer value
    content = request.form['content']

    # Insert the review into the database
    review_data = {
        'userId': user_id,
        'bookId': int(book_id),
        'content': content,
        'ratings': ratings
    }
    reviews_collection.insert_one(review_data)
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/')
def index():
    explain_result = books_collection.find(
        {"title": "Ella  : A novel. Diane Richards."}
    ).explain()

    # Print the explain result
    print(explain_result)
    try:
        # Check if a search query is provided
        query = request.args.get('search', '')

        if query:
            # Filter books with a case-insensitive search on title
            books = list(books_collection.find({"title": {"$regex": query, "$options": "i"}}))
        else:
            # Fetch all books if no search query
            #books = list(books_collection.find())
            books = list(books_collection.find().sort("id", pymongo.ASCENDING))
    except Exception as e:
        print(f"An error occurred: {e}")
        books = []
    
    return render_template("index.html", books=books)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():  # When the form is submitted
        email = form.email.data
        password = form.password.data

        # Query to find user by email
        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user['password'], password):  # Verify password
            # Set session variables
            session['user_id'] = user['userId'] # Store user ID as a string
            session['email'] = user['email']
            session['user_type'] = user['user_type']

            flash('Login successful!', 'success')

            # Redirect based on user type
            if user['user_type'] == 'a':  # Admin
                return redirect(url_for('admin_index'))
            elif user['user_type'] == 'u':  # Regular user
                return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():  # Validate form submission
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        hashed_password = generate_password_hash(password)

        # Define user type
        user_type = 'u'  # For regular users
        fees_due = 0.00
        user_count = users_collection.count_documents({})
        user_id = user_count +1
        # Create a new user document
        user_data = {
            'userId' : user_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': hashed_password,
            'fees_due': fees_due,
            'user_type': user_type
        }

        try:
            # Insert user data into the MongoDB collection
            users_collection.insert_one(user_data)
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as err:
            flash(f"Error: {err}", 'danger')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    # Clear the user session
    session.clear()  # This logs out the user by clearing their session data
    flash('You have been logged out.', 'info')  # Display a message
    return redirect(url_for('login'))  # Redirect to the login page


@app.route('/admin_index', methods=['GET', 'POST'])
def admin_index():
    try:
        # Get the search query from the request arguments
        query = request.args.get('search', '')

        # Check if a search query is provided
        if query:
            # Filter books with a case-insensitive search on title
            books = list(books_collection.find({"title": {"$regex": query, "$options": "i"}}))
        else:
            # Fetch all books if no search query
            books = list(books_collection.find().sort("id", pymongo.ASCENDING))

        # Convert `_id` (ObjectId) to string for compatibility with the template
        for book in books:
            book['_id'] = str(book['_id'])
            
            # Format createdDate if it's a datetime object
            if 'createdDate' in book and isinstance(book['createdDate'], datetime):
                book['createdDate'] = book['createdDate'].strftime("%Y-%m-%d")

    except Exception as e:
        print(f"An error occurred while loading books: {e}")
        books = []

    # Render the admin_index.html template with the books
    return render_template("admin_index.html", books=books, search_query=query)





@app.route('/book/<string:book_id>')
def book_detail(book_id):
    if 'user_id' not in session:
        flash('You need to log in to access your account.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    with safe_db_operation():
        # Atomic operation to get book and borrow status
        book = books_collection.find_one({'id': int(book_id)})
        
        if book is None:
            return "Book not found", 404

        book_id = int(book_id)
        user_id = int(user_id)

        # Use a single query to check borrow status
        borrow_status = borrow_collection.find_one(
            {'book_id': book_id, 'is_returned': 0},
            {'user_id': 1}
        )

        is_borrowed_by_user = borrow_status and borrow_status['user_id'] == user_id
        is_borrowed_by_anyone = borrow_status is not None

        # Rest of your existing code...
        reviews = list(db['Review'].find({'bookId': int(book_id)}))
        user_ids = [review['userId'] for review in reviews]
        users = {user['userId']: user for user in db['User'].find({'userId': {'$in': user_ids}})}

        reviews_data = [{
            'content': review['content'],
            'ratings': review.get('ratings', 0),
            'first_name': users.get(review['userId'], {}).get('first_name', ''),
            'last_name': users.get(review['userId'], {}).get('last_name', '')
        } for review in reviews]

        valid_ratings = [review['ratings'] for review in reviews_data if isinstance(review['ratings'], (int, float))]
        avg_rating = round(sum(valid_ratings) / len(valid_ratings), 1) if valid_ratings else None

        book_dict = {
            'id': book['id'],
            'title': book['title'],
            'abstract': book['abstract'],
            'languages': book['languages'],
            'published_date': book['createdDate'],
            'coverURL': book['coverURL'],
            'review_count': len(reviews_data),
            'avg_rating': avg_rating,
            'is_borrowed_by_user': is_borrowed_by_user,
            'is_borrowed_by_anyone': is_borrowed_by_anyone
        }

        return render_template("book.html", book=book_dict, form=ReviewForm(), reviews=reviews_data)




@app.route('/history')
def user_history():
    user_id = session['user_id']

    # Fetch borrow history for the user
    borrow_history = list(borrow_collection.aggregate([
        {
            '$match': {
                #'user_id': ObjectId(user_id)  # Ensure user_id is an ObjectId
                'user_id': user_id
            }
        },
        {
            '$lookup': {
                'from': 'Book',
                'localField': 'book_id',
                'foreignField': 'id',
                'as': 'book_details'
            }
        },
        {
            '$unwind': '$book_details'
        },
        {
            '$project': {
                'title': '$book_details.title',
                'borrow_date': 1,
                'due_date': 1,
                'return_date': 1,
                'is_returned': 1
            }
        }
    ]))



    current_date = datetime.now()

    # Calculate overdue days and fees
    for record in borrow_history:
        due_date = record['due_date']
        return_date = record['return_date']

        # Determine the date to compare for overdue calculation
        if record['is_returned']:
            comparison_date = return_date
        else:
            comparison_date = current_date

        overdue_days = (comparison_date - due_date).days
        record['overdue_days'] = max(0, overdue_days)
        record['overdue_fees'] = record['overdue_days'] * 1  # $1 per day overdue

    #client.close()
    return render_template('history.html', borrow_history=borrow_history)


@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('You need to log in to access your account.', 'danger')
        return redirect(url_for('login'))

    #email = session['email']
    user_id = session['user_id']
    user = users_collection.find_one({'userId': user_id})

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    #client.close()
    return render_template('account.html', user=user)


@app.route('/updateProfile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('You need to log in to update your profile.', 'danger')
        return redirect(url_for('login'))

    email = session['email']
    user_id = session['user_id']
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    new_email = request.form['email']


    # Update the user's information in the database
    update_result = users_collection.update_one(
        {'userId': user_id},
        {'$set': {
            'first_name': first_name,
            'last_name': last_name,
            'email': new_email
        }}
    )

    if update_result.modified_count > 0:
        # Update the session with the new email if it has been changed
        if email != new_email:
            session['email'] = new_email

        flash('Profile updated successfully!', 'success')
    else:
        flash('No changes made to the profile.', 'warning')

    #client.close()
    return redirect(url_for('account'))


from datetime import datetime, timedelta

@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    user_id = session['user_id']

    with borrow_lock:  # Thread-safe block
        try:
            # Atomic find-and-modify operation
            book_status = borrow_collection.find_one_and_update(
                {
                    "book_id": book_id,
                    "is_returned": 0
                },
                {
                    "$setOnInsert": {
                        "borrow_id": borrow_collection.count_documents({}) + 1,
                        "user_id": user_id,
                        "book_id": book_id,
                        "borrow_date": datetime.now(),
                        "due_date": datetime.now() + timedelta(days=14),
                        "return_date": None,
                        "is_returned": 0
                    }
                },
                upsert=True,
                return_document=ReturnDocument.BEFORE
            )

            if book_status and book_status.get('user_id') != user_id:
                flash('Book is currently borrowed by someone else.', 'danger')
            else:
                flash('You have successfully borrowed the book!', 'success')

        except Exception as e:
            flash(f'Error occurred while borrowing: {str(e)}', 'danger')
            return redirect(url_for('book_detail', book_id=book_id))

    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    user_id = session['user_id']

    with borrow_lock:  # Thread-safe block
        try:
            # Atomic find-and-modify operation
            result = borrow_collection.find_one_and_update(
                {
                    "book_id": book_id,
                    "user_id": user_id,
                    "is_returned": 0
                },
                {
                    "$set": {
                        "return_date": datetime.now(),
                        "is_returned": 1
                    }
                },
                return_document=ReturnDocument.AFTER
            )

            if result:
                flash('You have successfully returned the book!', 'success')
            else:
                flash('Error: Book return failed or book was not borrowed by you.', 'danger')

        except Exception as e:
            flash(f'Error occurred while returning: {str(e)}', 'danger')

    return redirect(url_for('user_history'))


from datetime import datetime

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = BookForm()

    if form.validate_on_submit():
        print("Form validated successfully!")
        print("Form data:", form.data)

        # Initialize cover_image_path to None
        cover_image_path = None

        # Handle file upload
        if form.cover_image_file.data:
            try:
                filename = secure_filename(form.cover_image_file.data.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                form.cover_image_file.data.save(filepath)
                cover_image_path = os.path.join('uploads', filename).replace('\\', '/')
            except Exception as e:
                flash(f"Error uploading file: {e}", 'danger')
                return redirect(url_for('add_book'))

        # Use the provided URL if no file was uploaded
        elif form.cover_image_url.data:
            cover_image_path = form.cover_image_url.data.strip()

        # Ensure at least one source of cover image is provided
        if not cover_image_path:
            flash("Please provide either a cover image file or URL.", "danger")
            return redirect(url_for('add_book'))

        # Convert createdDate to datetime.datetime
        created_date = form.createdDate.data
        if created_date:  # Only convert if a date is provided
            created_date = datetime.combine(created_date, datetime.min.time())

        # Prepare the book data
        book_data = {
            "title": form.title.data,
            "types": form.types.data,
            "authors": form.authors.data,
            "abstract": form.abstract.data,
            "languages": form.languages.data,
            "createdDate": created_date,  # Insert the converted datetime.datetime object
            "coverURL": cover_image_path,
            "subjects": form.subjects.data,
            "isbns": form.isbns.data,
        }

        try:
            books_collection.insert_one(book_data)
            flash("Book added successfully!", "success")
            print(f"Book data inserted: {book_data}")
            return redirect(url_for('admin_index'))
        except Exception as e:
            flash(f"Error saving book: {e}", "danger")
            print(f"Error inserting book data: {e}")
            return redirect(url_for('add_book'))

    print("Form validation failed.")
    print("Form errors:", form.errors)
    return render_template('add_book.html', form=form)




@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
    try:
        # Ensure the book ID is valid
        if not ObjectId.is_valid(book_id):
            flash("Invalid book ID.", "danger")
            return redirect(url_for('admin_index'))

        # Attempt to delete the book from the database
        result = books_collection.delete_one({'_id': ObjectId(book_id)})
        
        if result.deleted_count > 0:
            flash("Book deleted successfully!", "success")
        else:
            flash("Book not found or could not be deleted.", "warning")
    except Exception as e:
        print(f"Error deleting book: {e}")
        flash("An error occurred while trying to delete the book.", "danger")
    
    return redirect(url_for('admin_index'))




from bson import ObjectId

from werkzeug.utils import secure_filename
import os

from datetime import datetime

@app.route('/edit_book/<book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if not ObjectId.is_valid(book_id):
        return "Invalid book ID", 400

    try:
        # Fetch the book to be edited
        book = books_collection.find_one({'_id': ObjectId(book_id)})
        if not book:
            return "Book not found", 404

        form = BookForm(data=book)

        if form.validate_on_submit():
            updated_data = {
                'title': form.title.data or book.get('title'),
                'types': form.types.data or book.get('types'),
                'authors': form.authors.data or book.get('authors'),
                'abstract': form.abstract.data or book.get('abstract'),
                'languages': form.languages.data or book.get('languages'),
                'subjects': form.subjects.data or book.get('subjects'),
                'isbns': form.isbns.data or book.get('isbns')
            }

            # Handle the date conversion
            if form.createdDate.data:  # If a date is provided
                updated_data['createdDate'] = datetime.combine(form.createdDate.data, datetime.min.time())
            else:
                updated_data['createdDate'] = book.get('createdDate')

            # Handle file upload if provided
            if form.cover_image_file.data:
                try:
                    filename = secure_filename(form.cover_image_file.data.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    form.cover_image_file.data.save(image_path)  # Save the uploaded file
                    updated_data['coverURL'] = os.path.join('uploads', filename).replace('\\', '/')
                except Exception as e:
                    flash(f"Error uploading file: {e}", 'danger')
                    return redirect(url_for('edit_book', book_id=book_id))

            # If no file is uploaded, use the URL provided (if any)
            elif form.cover_image_url.data:
                updated_data['coverURL'] = form.cover_image_url.data.strip()

            # If neither file nor URL is provided, retain the existing coverURL
            else:
                updated_data['coverURL'] = book.get('coverURL')

            # Update the book in the database
            books_collection.update_one({'_id': ObjectId(book_id)}, {'$set': updated_data})
            flash('Book updated successfully!', 'success')
            return redirect(url_for('admin_index'))

        return render_template('edit_book.html', form=form, book_id=book_id, book=book)
    except Exception as e:
        print(f"Error editing book: {e}")
        return "An error occurred while editing the book.", 500







from bson import ObjectId

@app.route('/adminbook/<book_id>')
def adminbook_detail(book_id):
    print(f"Book ID received: {book_id}")  # Debugging

    try:
        # Ensure the book ID is valid
        if not ObjectId.is_valid(book_id):
            return "Invalid book ID", 400

        # Fetch the book from the database
        book = books_collection.find_one({'_id': ObjectId(book_id)})

        if not book:
            return "Book not found", 404

        # Convert the ObjectId to a string for template compatibility
        book['_id'] = str(book['_id'])

        print(f"Book fetched: {book}")  # Debugging

        return render_template("adminbook_details.html", book=book)
    except Exception as e:
        print(f"Error accessing book: {e}")
        return "An error occurred while fetching the book details.", 500





@app.route('/search_books', methods=['GET'])
def search_books():
    # Get the search query from the URL parameters
    query = request.args.get('search', '')

    # Filter books from the database
    if query:
        # Search for titles that contain the query (case-insensitive)
        books = books_collection.find({"title": {"$regex": query, "$options": "i"}})
    else:
        # If no query, return all books
        books = books_collection.find()

    # Render the index page with the filtered books
    return render_template('index.html', books=books)


if __name__ == "__main__":
    create_admin_user()
    app.run(host="0.0.0.0", port=5000, debug=True)