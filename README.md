# YouTube-DMCA-Project
My first CS project aimed at improving the process of finding copyright infringing videos on YouTube. This is the original code I wrote for the assignment built using the Harvard University IDE, so it will need some modifications to run (plus my API key is likely inactive by now). To see a run through of the functionality, go to: https://youtu.be/vmGxZVWdqbI

(Note: This app is mainly focused on the discovery and tracking of infringing videos. I know that the email template is not the proper method for submitting takedown requests.)


# Documentation for YouTube DMCAs

1. Install the program's dependencies (within project folder)
    pip3 install --user -r requirements.txt
    (If you don't install this way, make sure you individually install Flask, Flask-Session, passlib, SQLAlchemy, 
    and google-api-python-client using pip3 or pip)

2. Start Flask’s built-in web server (within project folder)
    flask run
    Open by clicking CS50 IDE in the top left -> Web Server

3. In another terminal window, start phpLiteAdmin (within project folder)
    phpliteadmin dmca.db
    Click the provided link to open the database

4. My API key should continue to run, however, if it does not, you will have to add your own key to helpers.py
    Go to https://console.developers.google.com/apis/credentials to create one (under credentials) and go to 
    helpers.py and add yours -> DEVELOPER_KEY = "YOUR_KEY"

5. View a video overview of the application at: https://youtu.be/vmGxZVWdqbI

6. View the site in the web server. Register an account in order to use the application.

7. Run a keyword search to query for video results from YouTube in order to find videos using your stolen work by typing the 
    keyword(s) into the search box and clicking "Search."

8. You may additionally run a search for related videos based on any selections made in the original search results by clicking 
    "Search Related."

9. Generate a DMCA email template with URLs for all of the selected infringing videos from that search included by clicking 
    "Get DMCA."

10. You can go to "History" to select from your previous search queries and view those videos. You can remove from 
    view any video that has been removed by YouTube.

11. You can view all saved user and search data in dmca.db
