from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

from flask import redirect, render_template, request, session, url_for
from functools import wraps

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyAo4TJN2CmVHCqSc-2XHnUv9E-SfQ2WPJ0"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def youtube_search(keywords):
    
    # set up YouTube API
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    try:
    # Call the search.list method to retrieve video results matching the keyword
        search_response = youtube.search().list(
            q=keywords,
            type="video",
            part="id,snippet",
            maxResults=20
        ).execute()
    except:
        return None

    results = []

    # Add each video to results list
    for result in search_response.get("items", []):
        result_info = {
            "title": result["snippet"]["title"],
            "videoId": result["id"]["videoId"],
            "channel": result["snippet"]["channelTitle"]
        }
        results.append(result_info)
    
    # return the results
    return results
 
 
def related_search(videoId):
    
    # set up YouTube API
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    
    try:
    # Call the search.list method to retrieve related results for the videoId
        search_response = youtube.search().list(
            relatedToVideoId=videoId,
            type="video",
            part="id,snippet",
            maxResults=10
        ).execute()
    except:
        return None

    results = []

    # Add each video to the results list
    for result in search_response.get("items", []):
        result_info = {
            "title": result["snippet"]["title"],
            "videoId": result["id"]["videoId"],
            "channel": result["snippet"]["channelTitle"]
        }
        results.append(result_info)
    
    # return results
    return results