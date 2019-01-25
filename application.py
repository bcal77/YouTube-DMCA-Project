from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///dmca.db")

@app.route("/")
@login_required
def index():
    return render_template("search.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", error="Must Provide Username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", error="Must Provide Password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return render_template("error.html", error="Invalid Username and/or Password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("search"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))
    
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # ensure email was submitted
        if not request.form.get("email"):
            return render_template("error.html", error="Missing Email")
        
        # ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", error="Missing Username")
        
        # ensure password was submitted
        if not request.form.get("password"):
            return render_template("error.html", error="Missing Password")
        
        # ensure password confirmation was submitted
        if not request.form.get("password2"):
            return render_template("error.html", error="Must Confirm Password")
        
        # ensure passwords are the same
        elif not request.form.get("password") == request.form.get("password2"):
            return render_template("error.html", error="Passwords Do Not Match")
        
        # query database for email
        rows = db.execute("SELECT * FROM users WHERE email = :email", email=request.form.get("email"))
        
        # ensure email doesn't already exist
        if len(rows) == 1:
            return render_template("error.html", error="Email Already Registered")
        
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # ensure username doesn't already exist
        if len(rows) == 1:
            return render_template("error.html", error="Username Already Exists")
        
        # hash password and insert info
        hashname = pwd_context.encrypt(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash, email) VALUES (:username, :hash, :email)", username=request.form.get("username"), hash=hashname, email=request.form.get("email"))
        
        # remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]
        
        # redirect user to home page
        return redirect(url_for("search"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search keywords on YouTube."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # display error if keyword(s) not submitted
        if not request.form.get("keywords"):
            return render_template("error.html", error="Missing Keyword(s)")
        
        # if keyword(s) submitted:
        else:
            user_id = session["user_id"]
            
            # add search query to search table
            db.execute("INSERT INTO search (user_id, keywords) VALUES (:user_id, :keywords)", user_id=user_id ,keywords=request.form.get("keywords"))
            
            # remember the search id
            rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
            search_id = rows[0]["MAX(id)"]
            
            # run search
            results = youtube_search(request.form.get("keywords"))
            
            # if no results, hide that query from user's search keywords and return error
            if results == None:
                db.execute("UPDATE search SET deleted=1 WHERE id = :id", id=search_id)
                return render_template("error.html", error="No Results Found")
            
            # otherwise, add results to results table
            for item in results:
                db.execute("""INSERT INTO results (search_id, title, videoId, channel)
                    VALUES (:search_id, :title, :videoId, :channel)""", search_id=search_id, 
                    title=item["title"], videoId=item["videoId"], channel=item["channel"])
            
            return redirect(url_for("results"))
    
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        
        # clear out non-infringing results if user clicked here after running a search
        db.execute("DELETE FROM results WHERE infringing = 0")
        
        return render_template("search.html")

@app.route("/results", methods=["GET", "POST"])
@login_required
def results():
    """Display interactive search results."""
    
    # if user reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        
        # remember user and search ids
        user_id = session["user_id"]
        rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
        search_id = rows[0]["MAX(id)"]
        
        # get data for search results and split into 2 sets
        data = db.execute("SELECT * FROM results WHERE search_id = :search_id", search_id=search_id)
        col2 = data[0:len(data)//2]
        col1 = data[len(data)//2:]
        
        return render_template("results.html", results1=col1, results2=col2)
    
    # if user submits form by clicking "Search Related"
    if request.method == 'POST' and 'related' in request.form:
        
        # remember user and search ids
        user_id = session["user_id"]
        rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
        search_id = rows[0]["MAX(id)"]
        
        # get a list of all the selected videos
        videoIds = request.form.getlist("check")
        
        # if none were selected
        if videoIds == []:
            
            # remove those results from results table
            db.execute("DELETE FROM results WHERE infringing = 0")
            # hide that keyword from user's searches
            db.execute("UPDATE search SET deleted=1 WHERE id = :id", id=search_id)
            # return error
            return render_template("error.html", error="No Results Selected")
            
        
        # if videos were selected
        else:    
            
            # iterate through each videoId in list
            for vid in videoIds:
                # mark as infringing
                db.execute("UPDATE results SET infringing=1 WHERE videoId = :videoId", videoId=vid)
            # delete non-infringing videos from results table
            db.execute("DELETE FROM results WHERE infringing = 0")
            
            # go to related search results page
            return redirect(url_for("related_results"))
    
    # if user submits form by clicking "Get DMCA"
    else:
        
        # remember user and search ids
        user_id = session["user_id"]
        rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
        search_id = rows[0]["MAX(id)"]
        
        # get a list of all the selected videos
        videoIds = request.form.getlist("check")
        
        # if none were selected   
        if videoIds == []:
            # remove those results from results table
            db.execute("DELETE FROM results WHERE infringing = 0")
            # hide that keyword from user's searches
            db.execute("UPDATE search SET deleted=1 WHERE id = :id", id=search_id)
            # return error
            return render_template("error.html", error="No Results Selected")
        
        # if any videos were selected
        else:    
            # iterate through each videoId in list
            for vid in videoIds:
                # mark as infringing
                db.execute("UPDATE results SET infringing=1 WHERE videoId = :videoId", videoId=vid)
            # delete non-infringing videos from results table
            db.execute("DELETE FROM results WHERE infringing = 0")
            
            # go to dmca page
            return redirect(url_for("dmca"))

@app.route("/related_results", methods=["GET", "POST"])
@login_required
def related_results():
    """Display interactive results for related video search."""
    
    # if user reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        
        # remember user and search ids
        user_id = session["user_id"]
        rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
        search_id = rows[0]["MAX(id)"]
        
        # get all of the infringing videoIds for that search query
        videoIds = db.execute("SELECT videoId FROM results WHERE search_id = :search_id", search_id=search_id)
        
        # search for related videos for each videoId and collect the details for each result
        related = []
        for vid in videoIds:
            information = related_search(vid["videoId"])
            for info in information:
                related_item = {"title": info["title"], "videoId": info["videoId"], "channel": info["channel"]}
                related.append(related_item)
        
        # if no results found, return dmca with only the results from the original search
        if related == []:
            return redirect(url_for("dmca"))
        
        # otherwise, add those results to results table, mark as related
        for item in related:
            db.execute("""INSERT INTO results (search_id, title, videoId, channel, related)
                VALUES (:search_id, :title, :videoId, :channel, :related)""", search_id=search_id, 
                title=item["title"], videoId=item["videoId"], channel=item["channel"], related=1)
        
        # get data for search results and split into 2 sets
        data = db.execute("SELECT * FROM results WHERE search_id = :search_id AND related=1", search_id=search_id)   
        col2 = data[0:len(data)//2]
        col1 = data[len(data)//2:]
        
        # render the related search results page
        return render_template("related_results.html", results1=col1, results2=col2)
    
    # if user reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        
        # remember user and search ids
        user_id = session["user_id"]
        rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
        search_id = rows[0]["MAX(id)"]
        
        # get a list of all of the selected videos
        videoIds = request.form.getlist("check")
        
        # if none were selected, delete those results, return dmca with the original search selections   
        if videoIds == []:
            db.execute("DELETE FROM results WHERE infringing = 0")
            return redirect(url_for("dmca"))
        
        # if any videos were selected
        else:    
            
            # interate through each videoId
            for vid in videoIds:
                # set as infringing in results table
                db.execute("UPDATE results SET infringing=1 WHERE videoId = :videoId", videoId=vid)
            
            # delete non-infringing results
            db.execute("DELETE FROM results WHERE infringing = 0")
            
            # unmark related videos
            db.execute("UPDATE results SET related=0 WHERE related=1")
            
            # go to dmca page
            return redirect(url_for("dmca"))

@app.route("/dmca")
@login_required
def dmca():
    """Display formatted email with infringing URLs."""
    
    # remember user and search ids
    user_id = session["user_id"]
    rows = db.execute("SELECT MAX(id) FROM search WHERE user_id = :user_id", user_id=user_id)
    search_id = rows[0]["MAX(id)"]
    
    # retrieve all of the infringing videos for that search id
    urls = db.execute("SELECT * FROM results WHERE search_id = :search_id", search_id=search_id)
    
    # render email template with urls of those infringing videos included
    return render_template("dmca.html", urls=urls)

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of user's keyword searches."""
    
    # if user reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        
        # remember user id
        user_id = session["user_id"]
        
        # clear out non-infringing results if user clicked here after running a search
        db.execute("DELETE FROM results WHERE infringing = 0")
        
        # get all of the unique search keywords from that user
        searches = db.execute("SELECT DISTINCT keywords FROM search WHERE user_id = :user_id AND deleted=0", user_id=user_id)
        
        # display these keywords as a dropdown form
        return render_template("history.html", searches=searches)
    
    # if user reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        
        # remember user id
        user_id = session["user_id"]
        
        # get keyword the user selected
        keywords = request.form["search_keyword"]
        
        # mark all instances this keyword was searched by the user
        db.execute("UPDATE search SET selected=1 WHERE keywords = :keywords AND user_id = :user_id", keywords=keywords, user_id=user_id)
        
        # go to history results page
        return redirect(url_for("history_results"))

@app.route("/history_results", methods=["GET", "POST"])
@login_required
def history_results():
    """Show user's results history for specific keyword."""
    
    # if user reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        
        # get all search ids for the selected keyword
        matches = db.execute("SELECT id FROM search WHERE selected = 1")
        search_ids = []
        for match in matches:
            search_ids.append(match["id"])
        
        # collect information for active history results for that keyword
        history = []
        for id in search_ids:
            information = (db.execute("SELECT * FROM results WHERE search_id = :search_id AND deleted=0", search_id=id))
            for info in information:
                hist_item = {"title": info["title"], "videoId": info["videoId"]}
                history.append(hist_item)
        
        # split the results into 2 sets to display to user 
        col2 = history[0:len(history)//2]
        col1 = history[len(history)//2:]
        
        # deselect all of these results in the search table
        db.execute("UPDATE search SET selected=0 WHERE selected=1")
        
        # display results 
        return render_template("history_results.html", history1=col1, history2=col2)
    
    # if user reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        
        # get list of all of the selected videos
        videoIds = request.form.getlist("check")
        
        # if none selected    
        if videoIds == []:
            # go back to main history page
            return redirect(url_for("history"))
        
        # if any videos were selected
        else:    
            # mark these videos as deleted in the results table
            for vid in videoIds:
                db.execute("UPDATE results SET deleted=1 WHERE videoId = :videoId", videoId=vid)
            
            # return to main history page
            return redirect(url_for("history"))