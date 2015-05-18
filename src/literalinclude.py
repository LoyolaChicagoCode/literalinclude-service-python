import json
import re
import base64

# pip install flask
from flask import *

# pip install requests
import requests

app = Flask(__name__)
app.debug = False


# request_wants_json() is adapted from http://flask.pocoo.org/snippets/45/

def request_wants_json():
  best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
  return best == 'application/json' \
    and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

def error_response(message):
  if request_wants_json():
    return jsonify(error=message)
  else:
    return Response(message, mimetype='text/plain')

def github_request(user, repo, path):
  return requests.get("https://api.github.com/repos/%(user)s/%(repo)s/contents/%(path)s" % vars())
  
def github_request_uri(user, repo, path):
  return r"https://api.github.com/repos/%(user)s/%(repo)s/contents/%(path)s" % vars()

def get_file_content(request):
  return request.json().get('content', '')

def get_file_text(b64data, encoding='utf-8'):
  data = base64.b64decode(b64data).decode(encoding)
  lines = data.split('\n')   # need to check this assumption
  return lines

def get_joined_lines(lines):
  return "\n".join(lines)

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
    return error_response("Cannot access " + github_request_uri(user, repo, path))
  file_content = get_file_content(r)
  file_text = get_file_text(file_content)
  file_rloc = len(file_text)
  default_line_selection = "%d-%d" % (1, file_rloc)
  lines = request.args.get('lines', default_line_selection)
  try:
    dedent = int(request.args.get('dedent', 0))
    if dedent < 0:
      return error_response("dedent must be a non-negative integer; %s found" % dedent)
  except:
    return error_response("dedent must be a non-negative integer; %s found" % request.args.get('dedent'))

  tokens = lines.split("-")
  if len(tokens) != 2:
    return error_response("Illegal line selection syntax (requires m-n; found %s; m and n <= %d)" % (lines, file_rloc))
  else:
    try:
      start_line = int(tokens[0])
      end_line = int(tokens[1])
    except:
      return error_response("line selection requires positive integers")
    if start_line not in range(1, file_rloc+1):
      return error_response("Illegal start line: %d" % start_line)
    if end_line not in range(1, file_rloc+1):
      return error_response("Illegal end line: %d" % end_line)
    out_lines = dedented_line_generator(file_text[start_line-1:end_line], dedent)
    joined_lines = get_joined_lines(out_lines)
    b64_lines = base64.b64encode(joined_lines.encode('utf-8'))
    if request_wants_json():
      return jsonify(service=service, user=user, type=type, repo=repo, path=path,
        start_line=start_line, end_line=end_line, text=b64_lines.decode('utf-8'))
    else:
      return Response(joined_lines, mimetype="text/plain")

#Running app on localhost
if __name__ == "__main__":
    app.run(port=5050)
