from flask import *
from flask_pymongo import PyMongo
from flask_compress import Compress
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import datetime
import os
import base64
import pyimgur

app = Flask(__name__)
app.url_map.strict_slashes = False

if "DYNO" not in os.environ:
    with open("apiTokens.txt") as apiToken:
        app.config.update(
            IMGUR_ID=apiToken.readline().strip().strip("Imgur_ID: "),
            MONGO_URI=apiToken.readline().strip().strip("MONGO_URI: "),
            SECRET_KEY=apiToken.readline().strip().strip("SECRET_KEY: ")
        )
else:
    app.config.update(
        IMGUR_ID=os.environ["IMGUR_ID"],
        MONGO_URI=os.environ["MONGO_URI"],
        SECRET_KEY=os.environ["SECRET_KEY"]
    )
app.config["ImgurObject"] = pyimgur.Imgur(app.config["IMGUR_ID"])
mongo = PyMongo(app)
Compress(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.before_request
def before_request():
    if 'DYNO' in os.environ:
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

@app.route("/")
def blogs():
    try:
        logged_in = session["logged_in"]
        if logged_in != {}:
            return render_template("blogs.html", login_status=dict(session["logged_in"]))
        else:
            return render_template("blogs.html", login_status=None)
    except:
        return render_template("blogs.html", login_status=None)


@app.route("/post_blog")
def post_blog():
    try:
        logged_in = session["logged_in"]
        if logged_in != {}:
            return render_template("post_blog.html", login_status=dict(session["logged_in"]))
        else:
            flash(Markup("""Please <a style="text-decoration: underline;" href="/login">Login</a> or <a style="text-decoration: underline;" href="/sign_up">Sign Up</a> to Post a Blog"""))
            return redirect("/")
    except:
        flash(Markup("""Please <a style="text-decoration: underline;" href="/login">Login</a> or <a style="text-decoration: underline;"  href="/sign_up">Sign Up</a> to Post a Blog"""))
        return redirect("/")


@app.route("/blog/<page>/")
def return_blog(page):
    results = mongo.db.blogs.find_one({"name": page+".html"})
    if results is None:
        abort(404)
    else:
        try:
            logged_in = session["logged_in"]
            if logged_in != {}:
                results["text"] = Markup(results["text"])
                return render_template("blog_template.html", results=results, login_status=dict(session["logged_in"]))
            else:
                return render_template("blog_template.html", results=results, login_status=None)
        except:
            return render_template("blog_template.html", results=results, login_status=None)


@app.route("/user/<user>/")
def return_use(user):
    results = mongo.db.users.find_one({"username": user})
    if results is None:
        abort(404)
    else:
        try:
            logged_in = session["logged_in"]
            if logged_in != {}:
                return render_template(f"user_template.html", results_from_user=results, login_status=dict(session["logged_in"]))
            else:
                return render_template(f"user_template.html", results_from_user=results)
        except:
            return render_template(f"user_template.html", results_from_user=results)

@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    try:
        logged_in = session["logged_in"]
        if logged_in != {}:
            flash("Already Logged In")
            return redirect("/")
        else:
            pass
    except:
        pass
    if request.method == "GET":
        return render_template("sign_up.html", login_status=None)
    elif request.method == "POST":
        if request.form["password"] == request.form["confirm_password"]:
            doc = {
                "first_name": request.form.get("first_name"), 
                "last_name": request.form.get("last_name"),
                "username": request.form.get("username"),
                "email": request.form.get("email").lower(),
                "password": request.form.get("password")
            }
            if mongo.db.users.find_one({"email": doc["email"]}) is None:
                session["logged_in"] = {
                    "first_name": doc["first_name"], 
                    "last_name": doc["last_name"],
                    "email": doc["email"],
                    "username": doc["username"]
                }

                mongo.db.users.insert_one(doc)
                
                flash("Successfully Signed Up")
                return redirect("/")
            else:
                flash("An Account is Already Registered with that Email")
                return redirect("/sign_up")
        else:
            flash("Confirm Password Does Not Match Password")
            return redirect("/sign_up")


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        logged_in = session["logged_in"]
        if logged_in != {}:
            flash("Already Logged In")
            return redirect("/")
        else:
            pass
    except:
        pass
    if request.method == "GET":
        return render_template("login.html", login_status=None)
    elif request.method == "POST":
        doc = {
            "email": request.form.get("email").lower(),
            "password": request.form.get("password")
        }
        found = mongo.db.users.find_one({"email": doc["email"], "password": doc["password"]})
        if found is not None:
            session["logged_in"] = {
                "first_name": found["first_name"], 
                "last_name": found["last_name"],
                "email": found["email"],
                "username": found["username"]
            }
            flash("Successfully Logged In")
            return redirect("/")
        else:
            flash("Incorrect Email or Password")
            return redirect("/login")


@app.route("/logout")
def logout():
    try:
        logged_in = session["logged_in"]
        if logged_in != {}:
            session["logged_in"] = {}
        else:
            flash("Not Logged In")
    except:
        flash("Not Logged In")
    
    return redirect("/")

@app.route("/api/blogs")
def api_blogs():
    to_return = []
    for blog in reversed(sorted(list(mongo.db.blogs.find({})), key=lambda date: datetime.datetime.strptime(date["date_released"]+date["time_released"], "%m/%d/20%y%H:%M:%S:%f"))):
        blog["_id"] = str(blog["_id"])
        blog["link"] = "https://blogger-101.herokuapp.com/" + blog["link"]
        to_return.append(blog)
    return jsonify(to_return)

@app.route("/api/add_blog_new", methods=["POST"])
def add_blog_new():
    title = request.form.get("blog_title")
    name = ("_".join(title.split(" "))).lower()
    to_upload_image = app.config["ImgurObject"]._send_request('https://api.imgur.com/3/image', method='POST', params={'image': base64.b64encode(request.files['file'].read())})
    doc = {
        "title": title,
        "user": request.form.get("user"),
        "name": name+".html",
        "text": request.form.get("blog_content"),
        "link": "/blog/%s" % name,
        "date_released": datetime.datetime.utcnow().strftime("%m/%d/%Y"),
        "time_released": datetime.datetime.utcnow().strftime("%H:%M:%S:%f"),
        "comments": [],
        "image": to_upload_image["link"]
    }
    mongo.db.blogs.insert_one(doc)
    return redirect("/")

@app.route("/api/check_user", methods=["POST"])
def check_user():
    email = (request.json["email"]).lower()
    password = request.json["password"]

    user_found = mongo.db.users.find_one({"email": email, "password": password}) 

    if user_found is not None:
        return {"found": True, "user_found": user_found["username"]}
    else:
        return {"found": False}


@app.route("/api/add_user", methods=["POST"])
def add_user():
    doc = {
        "first_name": request.json.get("first_name"), 
        "last_name": request.json.get("last_name"),
        "username": request.json.get("username"),
        "email": request.json.get("email"),
        "password": request.json.get("password")
    }
    if mongo.db.users.find_one({"email": doc["email"]}) is None:
        if mongo.db.users.find_one({"username": doc["username"]}) is None:
            mongo.db.users.insert_one(doc)
            return {"success": True, "already": None}
        else:
            return {"success": False, "already": "username"}
    else:
        if mongo.db.users.find_one({"username": doc["username"], "email": doc["email"]}) is not None:
            return {"success": False, "already": "both"}
        else:
            return {"success": False, "already": "email"}


@app.route("/api/add_comment/", methods=["POST"])
def add_comment():
    blog = request.json["blog_title"]
    comment_type = request.json["type"]
    comment_content = "&zwnj;"+request.json["comment_content"]
    blog_found = mongo.db.blogs.find_one({"title": blog})
    if blog_found != None:
        if comment_type == "main":
            _id = mongo.db.comments.insert_one({"comment": comment_content, "user" : request.json["user"]})
            comments_tmp = blog_found["comments"]
            comments_tmp.append([str(_id.inserted_id), []])
            mongo.db.blogs.update_one({"title": blog}, {"$set": {"comments": comments_tmp}})
            return {"worked": True}
        else:
            id_of_comment = request.json["id"]
            if bool(len([True for i in blog_found["comments"] if i[0]==id_of_comment])):
                _id = mongo.db.comments.insert_one({"comment": comment_content, "user" : request.json["user"]})
                _id = str(_id.inserted_id)
                comments_tmp = blog_found["comments"]
                comments_tmp[[comments_tmp.index(i) for i in comments_tmp if i[0]==request.json["id"]][0]][1].append(_id)
                mongo.db.blogs.update_one({"title": blog}, {"$set": {"comments": comments_tmp}})
                return {"worked": True}
            else:
                return {"worked": False}
    else:
        return {"worked": False}


@app.route("/api/get_blog_comments", methods=["POST"])
def get_comments():
    if mongo.db.blogs.find_one({"title": request.json.get("blog_title")}) is not None:
        comments = mongo.db.blogs.find_one({"title": request.json.get("blog_title")})["comments"]
        commentsToShow = []
        for comment in comments:
            toAppend = []
            returned = mongo.db.comments.find_one({"_id": ObjectId(str(comment[0]))})
            toAppend.append(returned["comment"])
            toAppend.append(returned["user"])
            toAppend.append(str(returned["_id"]))
            toAppend2 = []
            for subComment in comment[1]:
                returned2 = mongo.db.comments.find_one({"_id": ObjectId(str(subComment))})
                toAppend2.append([returned2["comment"], returned2["user"]])
            toAppend.append(toAppend2)
            commentsToShow.append(toAppend)
        return {"found": commentsToShow, "number_of_comments": len(commentsToShow)}
    else:
        return {"found": False}

@app.errorhandler(HTTPException)
def page_not_found(e):
    flash("Page Not Found")
    return render_template("error.html", year=datetime.date.today().year, error=e)


def list_blogs():
    return reversed(sorted(list(mongo.db.blogs.find({})), key=lambda date: datetime.datetime.strptime(date["date_released"]+date["time_released"], "%m/%d/20%y%H:%M:%S:%f")))


app.add_template_global(datetime.date, name="date")
app.add_template_global(list_blogs, name="find_blogs")



if __name__ == "__main__":
    app.run(debug=("DYNO" not in os.environ), threaded=True)
