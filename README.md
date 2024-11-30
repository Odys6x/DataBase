# Library

## MongoDB

![Alt text](image/MongoDB.png)

![Alt text](image/MongoDB2.png)

## Python

### app.py

1. This is where you will run the code from to initialise the website.
2. This website is done by flask so its mostly routing in the backend like this.

   ![Alt text](image/app.jpg)

   as you can see here in @app.route('/login') it handles everything for login.html. So meaning to say if you were to look up to @app.route('/'), you can handle python logic and return any data, etc back to the html file it was assigned to.
   so to get started, go to app.py and run it.

### request.py

1. This is where you will run the code from to populate json files that contain NLB library books that are in ebook or digital.
2. If you want to populate your own json file, you can change the values of "ContentType". Eg. if you choose eBooks, it will gather 100 books of each category from categories.py.
   
   ![Alt text](image/request.jpg)
   
   these values are from the image below
   
   ![Alt text](image/ContentType.jpg)

### conn.py

This file will be the place to initialise our connection with our database. Change the password to the 'newpassword'.

### query.py

Query.py will contain long sql queries such that our app.py won't be so long.

## html

### base.html
![Alt text](image/Header.jpg)

### index.html
![Alt text](image/Content.jpg)

the {% block body %}{% endblock %} from base.html serves it purpose as a template for other html to use and if a html class uses {% extends 'base.html' %}, it means that it is populating it's own content with base.html.
