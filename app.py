from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from util import get_readme, get_repos, get_commits, get_commit, get_refs, get_tree, get_blob, create_bare_repo, search_commits
from pathlib import Path
from datetime import datetime
from db import init_db, verify_user
import re

app = Flask(__name__)
app.secret_key = '1234' # safe

init_db()

def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if 'username' not in session:
            flash('log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return check_login

repoRoot = Path("/home/lhietala/git-webview/repos-example")

# full date
@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    if isinstance(value, (int, float)):
        value = datetime.fromtimestamp(value)
    return value.strftime(format)

# highlight search terms (for search results)
@app.template_filter('highlight')
def highlight_filter(text, search_term):
    if not search_term or not text:
        return text
    # case insensitive regex
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark>{m.group()}</mark>', text)

# relative age
@app.template_filter('age')
def format_age(value):
    if isinstance(value, (int, float)):
        value = datetime.fromtimestamp(value)
    
    # ignore timezone
    if value.tzinfo is not None:
        value = value.replace(tzinfo=None)
    
    now = datetime.now()
    difference = now - value

    seconds = difference.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:  # 1 hour
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400: # 24 hours
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif seconds < 604800:  # 7 days
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''}"
    else:
        return value.strftime('%Y-%m-%d')

@app.route("/")
def index():
    repos = get_repos(repoRoot)
    return render_template("index.html", 
                           repos=repos)

@app.route("/<repo_name>/")
def repo_index(repo_name):
    ref = request.args.get('ref', 'HEAD')
    commits = get_commits(str(repoRoot / repo_name), ref=ref)
    refs = get_refs(str(repoRoot / repo_name))
    
    return render_template("commits.html", 
                           repo_name=repo_name, 
                           commits=commits,
                           branches=refs["branches"],
                           tags=refs["tags"],
                           ref=ref)

@app.route("/<repo_name>/readme")
def readme(repo_name):
    ref = request.args.get('ref', 'HEAD')
    readme = get_readme(str(repoRoot / repo_name), ref)
    refs = get_refs(str(repoRoot / repo_name))
    
    return render_template("readme.html", 
                           repo_name=repo_name, 
                           readme=readme,
                           branches=refs["branches"],
                           tags=refs["tags"],
                           ref=ref)

@app.route("/<repo_name>/commits")
def commits(repo_name):
    page = request.args.get('page', 1, type=int)
    ref = request.args.get('ref', 'HEAD')
    per_page = 50
    skip = (page - 1) * per_page
    
    commits = get_commits(str(repoRoot / repo_name), max_count=per_page, skip=skip, ref=ref)
    refs = get_refs(str(repoRoot / repo_name))
    
    has_next = len(commits) == per_page
    has_prev = page > 1
    
    return render_template("commits.html", 
                         repo_name=repo_name, 
                         commits=commits, 
                         page=page, 
                         has_next=has_next, 
                         has_prev=has_prev,
                         branches=refs["branches"],
                         tags=refs["tags"],
                         ref=ref)

@app.route("/<repo_name>/commit/<commit_hash>")
def commit(repo_name, commit_hash):
    commit = get_commit(str(repoRoot / repo_name), commit_hash)
    refs = get_refs(str(repoRoot / repo_name))
    
    return render_template("commit.html", 
                           repo_name=repo_name, 
                           commit=commit["commit"],
                           diffs=commit["diffs"],
                           branches=refs["branches"],
                           tags=refs["tags"])

@app.route("/<repo_name>/refs")
def refs(repo_name):
    ref = request.args.get('ref', 'HEAD')
    refs = get_refs(str(repoRoot / repo_name))
    
    return render_template("refs.html", 
                           repo_name=repo_name, 
                           branches=refs["branches"],
                           tags=refs["tags"],
                           ref=ref)

@app.route('/<repo_name>/tree')
@app.route('/<repo_name>/tree/<path:tree_path>')
def tree(repo_name, tree_path=""):
    ref = request.args.get('ref', 'HEAD')
    tree_data = get_tree(str(repoRoot / repo_name), tree_path, ref)
    refs = get_refs(str(repoRoot / repo_name))
    
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
                           ref=ref,
                           branches=refs["branches"],
                           tags=refs["tags"])

@app.route('/<repo_name>/blob/<path:blob_path>')
def blob(repo_name, blob_path):
    ref = request.args.get('ref', 'HEAD')
    blob = get_blob(str(repoRoot / repo_name), blob_path, ref)
    refs = get_refs(str(repoRoot / repo_name))
    
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
                           ref=ref,
                           branches=refs["branches"],
                           tags=refs["tags"])

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_repo():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Repository name is required', 'error')
            return render_template('create_repo.html')
        
        # TODO: proper validation
        if '/' in name or '\\' in name or '..' in name:
            flash('Invalid repository name', 'error')
            return render_template('create_repo.html')
        
        result = create_bare_repo(str(repoRoot), name, description)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('index'))
        else:
            flash(result['message'], 'error')
            return render_template('create_repo.html', name=name, description=description)
    
    return render_template('create_repo.html')

@app.route('/<repo_name>/search')
def search(repo_name):
    query = request.args.get('query', '').strip()
    ref = request.args.get('ref', 'HEAD')
    refs = get_refs(str(repoRoot / repo_name))
    
    results = []
    if query:
        results = search_commits(str(repoRoot / repo_name), query, ref)
    
    return render_template('search.html',
                         repo_name=repo_name,
                         query=query,
                         results=results,
                         branches=refs["branches"],
                         tags=refs["tags"],
                         ref=ref)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()