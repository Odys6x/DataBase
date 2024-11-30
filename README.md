# Library

## Important 
To access the admin functionalities, please login to the website with this credential:
Admin email: admin@email.com password:admin1234


## Python

### app.py

1. This is where you will run the code from to initialise the website.
2. This website is done by flask so its mostly routing in the backend like this.

   ![Alt text](image/app.jpg)

   as you can see here in @app.route('/login') it handles everything for login.html. So meaning to say if you were to look up to @app.route('/'), you can handle python logic and return any data, etc back to the html file it was assigned to.

So to get started, go to terminal and run this to get the proper version for the libraries we using.

```bash
   pip3 install -r requirements.txt
```

Once done, run the app.py and it will take awhile to load.

If you are curious where the API call are being handled is in request.py below vv

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

## MongoDB

![Alt text](image/MongoDB.png)

![Alt text](image/MongoDB2.png)

Select add new connection in Mongodb Compass. Install MongodbCompass before you do this.

![Alt text](image/mongo_1.png)

Enter the URI as shown in the image mongodb+srv://Admin:newpassword@mydb.9hyfl.mongodb.net/ and select save and connect.

![Alt text](image/mongo_2.png)

You have successfully connect to MongoDB and you can see the data under LibraryDB.

![Alt text](image/mongo_3.png)
