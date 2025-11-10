from flask import Flask, render_template, request
from util import get_readme, get_repos, get_commits, get_commit, get_refs, get_tree, get_blob
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

repoRoot = Path("/home/lhietala/git-webview/repos-example")

@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    if isinstance(value, (int, float)):
        value = datetime.fromtimestamp(value)
    return value.strftime(format)

@app.route("/")
def index():
    repos = get_repos(repoRoot)
    return render_template("index.html", 
                           repos=repos)

@app.route("/<repo_name>/")
def repo_index(repo_name):
    commits = get_commits(str(repoRoot / repo_name))
    return render_template("commits.html", 
                           repo_name=repo_name, 
                           commits=commits)

@app.route("/<repo_name>/readme")
def readme(repo_name):
    readme = get_readme(str(repoRoot / repo_name))
    return render_template("readme.html", 
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

@app.route("/<repo_name>/commit/<commit_hash>")
def commit(repo_name, commit_hash):
    commit = get_commit(str(repoRoot / repo_name), commit_hash)
    
    return render_template("commit.html", 
                           repo_name=repo_name, 
                           commit=commit["commit"],
                           diffs=commit["diffs"])

@app.route("/<repo_name>/refs")
def refs(repo_name):
    refs = get_refs(str(repoRoot / repo_name))
    
    return render_template("refs.html", 
                           repo_name=repo_name, 
                           branches=refs["branches"],
                           tags=refs["tags"])

@app.route('/<repo_name>/tree')
@app.route('/<repo_name>/tree/<path:tree_path>')
def tree(repo_name, tree_path=""):
    ref = request.args.get('ref', 'HEAD')
    tree_data = get_tree(str(repoRoot / repo_name), tree_path, ref)
    
    path_parts = []
    if tree_path:
        parts = tree_path.split('/')
        current_path = ""
        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part
            path_parts.append({"name": part, "path": current_path})
    
    return render_template("tree.html", 
                           repo_name=repo_name,
                           tree=tree_data,
                           path_parts=path_parts,
                           current_path=tree_path,
                           ref=ref)

@app.route('/<repo_name>/blob/<path:blob_path>')
def blob(repo_name, blob_path):
    ref = request.args.get('ref', 'HEAD')
    blob = get_blob(str(repoRoot / repo_name), blob_path, ref)
    
    path_parts = []
    if blob_path:
        parts = blob_path.split('/')
        current_path = ""
        for i, part in enumerate(parts[:-1]):  # exclude the file name, only dirs are linked in template
            current_path = f"{current_path}/{part}" if current_path else part
            path_parts.append({"name": part, "path": current_path})
    
    return render_template("blob.html", 
                           repo_name=repo_name,
                           blob=blob,
                           path_parts=path_parts,
                           ref=ref)

if __name__ == "__main__":
    app.run()