from flask import Flask, render_template, request
from util import get_readme, get_repos, get_commits
from pathlib import Path

app = Flask(__name__)

repoRoot = Path("/home/lhietala/git-webview/repos-example")

@app.route("/")
def index():
    repos = get_repos(repoRoot)
    return render_template("index.html", 
                           repos=repos)

@app.route("/<repo_name>/")
def summary(repo_name):
    commits = get_commits(str(repoRoot / repo_name))
    return render_template("summary.html", 
                           repo_name=repo_name, 
                           commits=commits)

@app.route("/<repo_name>/about")
def about(repo_name):
    readme = get_readme(str(repoRoot / repo_name))
    return render_template("about.html", 
                           repo_name=repo_name, 
                           readme=readme)

@app.route("/<repo_name>/commits")
def commits(repo_name):
    page = request.args.get('page', 1, type=int)
    per_page = 50
    skip = (page - 1) * per_page
    
    commits = get_commits(str(repoRoot / repo_name), max_count=per_page, skip=skip)
    
    has_next = len(commits) == per_page
    has_prev = page > 1
    
    return render_template("commits.html", 
                         repo_name=repo_name, 
                         commits=commits, 
                         page=page, 
                         has_next=has_next, 
                         has_prev=has_prev)

if __name__ == "__main__":
    app.run()