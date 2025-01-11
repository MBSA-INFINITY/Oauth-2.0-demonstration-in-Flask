from flask import Flask, request, render_template, redirect, abort, session, flash
import os
import uuid
from datetime import datetime
import requests
import pathlib
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from client_secret import client_secret

app = Flask(__name__)
app.secret_key = "mbsaiaditya"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']

flow = Flow.from_client_config(
    client_config=client_secret,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


@app.route("/", methods = ['GET'])
def start():
    if session.get('google_id') is not None:
        return redirect('/dashboard')
    return render_template("index.html")

    

@app.route("/dashboard", methods = ['GET'])
def dashboard():
    if session.get('google_id') is None:
        return redirect('/')
    return "You are logged in as " + session["name"]

@app.route("/login")
def login():
    if session.get('google_id') is None:
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)
    else:
        flash({'type':'error', 'data':"Your are already Logged In"})
        return redirect("/")
        

@app.route("/logout", methods = ['GET'])
def logout():
    if "google_id" not in session:
        return redirect("/")
    session.pop("google_id")
    session.pop("name")
    return redirect("/")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    print(id_info)

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    return redirect("/")

if __name__ == '__main__': 
    app.run(debug=True)