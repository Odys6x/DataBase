create_table = """
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
    password VARCHAR(30) NOT NULL,
    fees_due DECIMAL(2, 2) DEFAULT 0.00,
    user_type CHAR(1) 
);
"""
