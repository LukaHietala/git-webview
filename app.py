from flask import Flask, render_template
from util import get_repos

app = Flask(__name__)

@app.route("/")
def index():
    repos = get_repos("/home/lhietala/git-webview/repos-example")
    return render_template("index.html", repos=repos)

if __name__ == "__main__":
    app.run()