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