#from pymongo import *

# included in Python
import json
import socket
import re
import base64

# pip install flask
from flask import *

# pip install requests
import requests

app = Flask(__name__)
app.debug = True

# Show available databases

# Some quick/dirty tests of Flask and templating (Hello, World)
# I need these examples for later work to add a presentation layer.
# Right now, most of our queries return text/plain for raw inclusion elsewhere.

@app.route("/hello/<person>/")
def hi_person(person="Mr. Nobody"):
  return render_template("hello.html", person=person)

@app.route("/greeting/<person>/")
def greet_person(person="Mr. Nobody"):
  message = request.args.get('message', "How are you?")
  return render_template("greeting.html", person=person, message=message)

  
def github_request(user, repo, path):
  return requests.get("https://api.github.com/repos/%(user)s/%(repo)s/contents/%(path)s" % vars())
  
def github_request_uri(user, repo, path):
  return r"https://api.github.com/repos/%(user)s/%(repo)s/contents/%(path)s" % vars()

# This is so we can access the base64 representation directly (only for development)
@app.route("/base64/<service>/<type>/<user>/<repo>/<path:path>")
def get_b64(service, type, user, repo, path):
  if service != 'github' or type != 'code':
    return Response("We only serve 'github' and 'code' requests")

  r = github_request(user, repo, path)
  if r.status_code == 200:
    b64data = r.json().get('content')
    return Response(b64data, mimetype='text/plain')
  else:
    return Response("Cannot access " + github_request_uri(user, repo, path))

# This is to get the actual file
@app.route("/file/<service>/<type>/<user>/<repo>/<path:path>")
def get_file(service, type, user, repo, path):
  if service != 'github' or type != 'code':
    return Response("We only serve 'github' and 'code' requests")

  r = github_request(user, repo, path)
  if r.status_code == 200:
    b64data = r.json().get('content')
    entire_file = base64.b64decode(b64data).decode('utf-8')
    return Response(entire_file, mimetype='text/plain')
  else:
    return Response("Cannot access " + github_request_uri(user, repo, path))

# This code balances the requested format with best available
# Used in the HIV web service but not needed here yet.

def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


#Running app on localhost
if __name__ == "__main__":
    app.run(port=5050)
