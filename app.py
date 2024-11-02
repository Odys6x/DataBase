import os
from bson import ObjectId
from flask import Flask, render_template, redirect, url_for, flash, session, request
from werkzeug.utils import secure_filename
from wtforms import TextAreaField, IntegerField, SubmitField, validators
import json
from flask_wtf import CSRFProtect, FlaskForm
from pymongo import MongoClient
from bookform import BookForm
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

client = MongoClient('mongodb+srv://Admin:newpassword@mydb.9hyfl.mongodb.net/')  # Connect to MongoDB
db = client['LibraryDB']  # Replace with your database name
books_collection = db['Book']  # Collection for books
users_collection = db['User']  # Collection for users
reviews_collection = db['Review']
borrow_collection = db['BorrowedList']

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
    try:
        # Fetch all books from the database to pass to the template
        books = list(books_collection.find())

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

        # Create a new user document
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': hashed_password,
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


@app.route('/admin_index')
def admin_index():
    with open('json/audio/nlb_api_response0.json') as file:
        data = json.load(file)

    try:
        # Check if the collection is empty
        if books_collection.count_documents({}) == 0:
            for book in data['results']:
                title = book['title'].replace('[electronic resource]', '').strip()
                types = ', '.join(book['types'])
                authors = ', '.join(book['authors'])
                abstract = ', '.join(book['abstracts'])
                languages = ', '.join(book['languages'])
                coverURL = book.get('coverUrl', '')
                subjects = book.get('subjects', [])
                isbns = ', '.join(book['isbns'])
                createdDate = book.get('createdDate')

                if createdDate:
                    createdDate = datetime.strptime(createdDate, "%Y-%m-%d").date()
                else:
                    createdDate = None

                # Create a document to insert
                book_document = {
                    'title': title,
                    'types': types,
                    'authors': authors,
                    'abstract': abstract,
                    'languages': languages,
                    'createdDate': createdDate,
                    'coverURL': coverURL,
                    'subjects': subjects,
                    'isbns': isbns
                }
                books_collection.insert_one(book_document)  # Insert the document into MongoDB

        # Fetch all books from the MongoDB collection
        books = list(books_collection.find())

    except Exception as err:
        print(f"Error: {err}")
        books = []

    return render_template("admin_index.html", books=books)

@app.route('/book/<string:book_id>')
def book_detail(book_id):
    user_id = session.get('user_id')  # Get user_id from the session

    # Fetch the book based on the ID
    book = books_collection.find_one({'id': int(book_id)})

    if book is None:
        return "Book not found", 404

    # Check if the book is borrowed by the current user
    is_borrowed_by_user = db['BorrowedList'].find_one(
        {'book_id': book_id, 'user_id': int(user_id), 'is_returned': False}) is not None

    # Check if the book is borrowed by any user (other than the current one)
    is_borrowed_by_anyone = db['BorrowedList'].find_one({'book_id': int(book_id), 'is_returned': False}) is not None

    # Fetch reviews related to the book
    reviews = list(db['Review'].find({'bookId': int(book_id)}))

    # Prepare a dictionary to hold user data for quick lookup
    user_ids = [review['userId'] for review in reviews]  # Get all user IDs from the reviews
    users = {user['userId']: user for user in db['User'].find({'userId': {'$in': user_ids}})}  # Fetch users in one go

    # Convert the reviews to a format compatible with your template
    reviews_data = [{
        'content': review['content'],
        'ratings': review.get('ratings', 0),  # Default to 0 if ratings are missing
        'first_name': users.get(review['userId'], {}).get('first_name', ''),  # Fetch first name from users dict
        'last_name': users.get(review['userId'], {}).get('last_name', '')  # Fetch last name from users dict
    } for review in reviews]


    # Calculate the average rating, ensuring we only include valid ratings
    valid_ratings = [review['ratings'] for review in reviews_data if isinstance(review['ratings'], (int, float))]
    avg_rating = round(sum(valid_ratings) / len(valid_ratings), 1) if valid_ratings else None

    # Prepare the book dictionary for rendering
    book_dict = {
        'id': book['id'],  # Keep the 'id' from the document
        'title': book['title'],
        'abstract': book['abstract'],
        'languages': book['languages'],
        'published_date': book['createdDate'],
        'coverURL': book['coverURL'],
        'review_count': len(reviews_data),  # Number of reviews
        'avg_rating': avg_rating,  # Use the calculated average rating
        'is_borrowed_by_user': is_borrowed_by_user,
        'is_borrowed_by_anyone': is_borrowed_by_anyone
    }

    # Render the template with book and review data
    return render_template("book.html", book=book_dict, form=ReviewForm(), reviews=reviews_data)




@app.route('/history')
def user_history():
    user_id = session['user_id']

    # Fetch borrow history for the user
    borrow_history = list(borrow_collection.aggregate([
        {
            '$match': {
                'user_id': ObjectId(user_id)  # Ensure user_id is an ObjectId
            }
        },
        {
            '$lookup': {
                'from': 'Book',
                'localField': 'book_id',
                'foreignField': '_id',
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

    current_date = datetime.now().date()

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

    client.close()
    return render_template('history.html', borrow_history=borrow_history)


@app.route('/account')
def account():
    if 'email' not in session:
        flash('You need to log in to access your account.', 'danger')
        return redirect(url_for('login'))

    email = session['email']

    user = users_collection.find_one({'email': email})

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    client.close()
    return render_template('account.html', user=user)


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
    update_result = users_collection.update_one(
        {'email': email},
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

    client.close()
    return redirect(url_for('account'))


@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    user_id = session['user_id']

    # Check if the book is already borrowed
    book_borrowed = borrow_collection.find_one({
        "book_id": book_id,
        "is_returned": False
    })

    if book_borrowed:
        flash('Book is currently borrowed by someone else.', 'danger')
        return redirect(url_for('book_detail', book_id=book_id))

    # If book is not borrowed, allow user to borrow
    borrow_date = datetime.now().date()
    due_date = borrow_date + timedelta(days=14)  # 2-week borrowing period

    borrow_document = {
        "user_id": user_id,
        "book_id": book_id,
        "borrow_date": borrow_date,
        "due_date": due_date,
        "is_returned": False
    }

    borrow_collection.insert_one(borrow_document)

    flash('You have successfully borrowed the book!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    user_id = session['user_id']

    return_date = datetime.now().date()

    result = borrow_collection.update_one(
        {
            "book_id": book_id,
            "user_id": user_id,
            "is_returned": False
        },
        {
            "$set": {
                "return_date": return_date,
                "is_returned": True
            }
        }
    )

    if result.modified_count > 0:
        flash('You have successfully returned the book!', 'success')
    else:
        flash('Error: Book return failed or book was not borrowed by you.', 'danger')

    return redirect(url_for('user_history'))



@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = BookForm()

    if form.validate_on_submit():
        title = form.title.data or None
        types = form.types.data or None
        authors = form.authors.data or None
        abstract = form.abstract.data or None
        languages = form.languages.data or None
        created_date = form.createdDate.data or None
        cover_image_path = None

        # Handle file upload if it exists
        if form.cover_image_file.data:
            filename = secure_filename(form.cover_image_file.data.filename)
            image_path = os.path.join('uploads', filename).replace('\\', '/')
            form.cover_image_file.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_image_path = image_path  # Use the file path as the cover image path
        elif form.cover_image_url.data:
            cover_image_path = form.cover_image_url.data  # Use the URL as the cover image

        subjects = form.subjects.data or None
        isbns = form.isbns.data or None

        book_data = {
            "title": title,
            "types": types,
            "authors": authors,
            "abstract": abstract,
            "languages": languages,
            "createdDate": created_date,
            "coverURL": cover_image_path,
            "subjects": subjects,
            "isbns": isbns
        }

        try:
            books_collection.insert_one(book_data)
            flash('Book added successfully!', 'success')
        except Exception as err:
            flash(f"Error: {err}", 'danger')

        return redirect(url_for('admin_index'))

    return render_template('add_book.html', form=form)


@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
    result = books_collection.delete_one({'_id': ObjectId(book_id)})

    if result.deleted_count > 0:
        flash('Book deleted successfully!', 'success')
    else:
        flash(f"No book found with ID {book_id}.", 'warning')

    return redirect(url_for('admin_index'))



@app.route('/edit_book/<book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = books_collection.find_one({'_id': ObjectId(book_id)})

    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for('admin_index'))

    form = BookForm(data=book)

    if form.validate_on_submit():
        updated_data = {
            'title': form.title.data or None,
            'types': form.types.data or None,
            'authors': form.authors.data or None,
            'abstract': form.abstract.data or None,
            'languages': form.languages.data or None,
            'createdDate': form.createdDate.data or None,
            'coverURL': form.cover_image_url.data or book['coverURL'],  # Keep existing URL if not changed
            'subjects': form.subjects.data or None,
            'isbns': form.isbns.data or None
        }

        # Handle file upload if provided
        if form.cover_image_file.data:
            filename = secure_filename(form.cover_image_file.data.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\', '/')
            form.cover_image_file.data.save(os.path.join('static', image_path))
            updated_data['coverURL'] = image_path

        books_collection.update_one({'_id': ObjectId(book_id)}, {'$set': updated_data})
        flash('Book updated successfully!', 'success')
        return redirect(url_for('adminbook_detail', book_id=book_id))

    return render_template('edit_book.html', form=form, book_id=book_id, book=book)


@app.route('/adminbook/<book_id>')
def adminbook_detail(book_id):
    book = books_collection.find_one({'_id': ObjectId(book_id)})

    if book is None:
        return "Book not found", 404

    return render_template("adminbook_details.html", book=book)


@app.route('/search', methods=['GET'])
def search_books():
    search_query = request.args.get('search', '')

    if not search_query:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('index'))

    books = books_collection.find({'title': {'$regex': search_query, '$options': 'i'}})

    if books.count() == 0:
        flash(f'No books found for "{search_query}".', 'info')
        return redirect(url_for('index'))

    return render_template('index.html', books=books, search_query=search_query)


if __name__ == "__main__":
    create_admin_user()
    app.run(debug=True)