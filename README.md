# Blogger101

This is a simple blogging website like Medium. 

To Run:

Prerequisites:

Python 3.3 and newer
Pip

Instructions:

Download this repo and unzip the folder. Then, `cd` into the folder, and run `pip install -r requirements.txt` to install the needed packages. After that, create an apiTokens.txt file with the following format:

```
Imgur_ID: [Imgur ID API Key Here]
MONGO_URI: [MongoDB Atlas (free tier will do) URL. Create a project, and collection with blogs, comments, and users. Get the url for the collection and paste it here. ]
SECRET_KEY: [A bunch of random letters used for encrypting the cookies. Something like "test123" will do for development, but make sure to use something longer and more complicated for production. ]
```

Then run `python app.py`. The website will be accessible on http://127.0.0.1:5000. 


When deploying to heroku, you do not need the apiTokens.txt file. Instead, put the Imgur ID, MongoDB Url, and Secret Key in heroku Config Vars, as IMGUR_ID, MONGO_URI, and SECRET_KEY. 
