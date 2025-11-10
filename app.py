from flask import Flask, render_template
from util import get_readme, get_repos
from pathlib import Path

app = Flask(__name__)

repoRoot = Path("/home/lhietala/git-webview/repos-example")

@app.route("/")
def index():
    repos = get_repos(repoRoot)
    return render_template("index.html", repos=repos)

@app.route("/<repo_name>/about")
def about(repo_name):
    readme = get_readme(str(repoRoot / repo_name))
    return render_template("about.html", readme=readme)

if __name__ == "__main__":
    app.run()