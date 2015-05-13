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

def get_file_content(request):
  return request.json().get('content', '')

def get_file_text(b64data, encoding='utf-8'):
  data = base64.b64decode(b64data).decode(encoding)
  lines = data.split('\n')   # need to check this assumption
  return lines

def get_joined_lines(lines):
  return "\n".join(lines)

@app.route("/base64/<service>/<type>/<user>/<repo>/<path:path>")
def get_b64(service, type, user, repo, path):
  r = github_request(user, repo, path)
  if r.status_code != 200:
    return Response("Cannot access " + github_request_uri(user, repo, path))
  b64data = get_file_content(r)
  return Response(b64data, mimetype='text/plain')

# This is to get the actual file
@app.route("/file/<service>/<type>/<user>/<repo>/<path:path>")
def get_file(service, type, user, repo, path):
  r = github_request(user, repo, path)
  if r.status_code != 200:
    return Response("Cannot access " + github_request_uri(user, repo, path))

  file_content = get_file_content(r)
  file_text = get_file_text(file_content)
  return Response(get_joined_lines(file_text), mimetype='text/plain')

# Beginning of actual include service!

def dedented_line_generator(lines, dedent_chars=0):
  for line in lines:
    try:
      yield line[dedent_chars:]
    except:
      yield ""

@app.route("/include/<service>/<type>/<user>/<repo>/<path:path>")
def do_include(service, type, user, repo, path):
  r = github_request(user, repo, path)
  if r.status_code != 200:
    return Response("Cannot access " + github_request_uri(user, repo, path))

  file_content = get_file_content(r)
  file_text = get_file_text(file_content)
  default_line_selection = "%d-%d" % (1, len(file_text))
  lines = request.args.get('lines', default_line_selection)
  try:
    dedent = int(request.args.get('dedent', 0))
  except:
    dedent = 0

  tokens = lines.split("-")
  if len(tokens) != 2:
    return Response("Illegal line selection: %s (must be m-n)" % lines, mimetype='text/plain')
  else:
    start_line = int(tokens[0])-1
    end_line = int(tokens[1])
    # TODO: need to ensure both of these are in range...
    out_lines = dedented_line_generator(file_text[start_line:end_line], dedent)
    return Response(get_joined_lines(out_lines), mimetype='text/plain')

#Running app on localhost
if __name__ == "__main__":
    app.run(port=5050)
