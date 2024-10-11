create_book_table = """
CREATE TABLE IF NOT EXISTS Book (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL UNIQUE,
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
create_user_table = """
CREATE TABLE IF NOT EXISTS User (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),  
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
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

