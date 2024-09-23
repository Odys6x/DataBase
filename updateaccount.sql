UPDATE User
SET FirstName = @FirstName, 
    LastName = @LastName,
    Email = @Email,
    Password = @Password -- Ensure to hash the password before storing
WHERE UserId = @UserId;
