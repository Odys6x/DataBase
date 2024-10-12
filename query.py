create_book_table = """
CREATE TABLE IF NOT EXISTS Book (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(300) NOT NULL UNIQUE,
    types VARCHAR(15),  -- Increased size to avoid truncation
    authors VARCHAR(50),
    abstract LONGTEXT,
    languages TEXT,
    createdDate DATE,
    coverURL VARCHAR(100),
    subjects VARCHAR(150),
    isbns VARCHAR(100)
);
"""

create_user_table = """
CREATE TABLE IF NOT EXISTS User (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(30),  
    last_name VARCHAR(30) NOT NULL,
    email VARCHAR(40) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    fees_due DECIMAL(2, 2) DEFAULT 0.00,
    user_type CHAR(1) 
);
"""

create_review_table = """
CREATE TABLE IF NOT EXISTS Review (
    reviewId INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each review
    userId INT NOT NULL,  -- References the User table
    bookId INT NOT NULL,  -- References the Book table
    content VARCHAR(255),  -- Review content
    ratings DECIMAL(2, 1),  -- Rating with one decimal point

    -- Foreign Key Constraints
    FOREIGN KEY (userId) REFERENCES User(userId) ON DELETE CASCADE,
    FOREIGN KEY (bookId) REFERENCES Book(id) ON DELETE CASCADE
);
"""
create_booklist_table = """
CREATE TABLE IF NOT EXISTS BorrowedList (
    borrow_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,  -- References the User table
    book_id INT NOT NULL,  -- References the Book table
    borrow_date DATE NOT NULL,  -- Date when the book was borrowed
    due_date DATE NOT NULL,  -- Due date for the book
    return_date DATE,  -- Actual return date
    is_returned BOOLEAN DEFAULT FALSE,  -- Whether the book is returned or not

    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES User(userId) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES Book(id) ON DELETE CASCADE
);
"""