from pathlib import Path
import git

def get_repos(repos_path=None):
    if repos_path is None:
        print("repo path not set")
        return []
    
    repos = []
    repos_path = Path(repos_path)
    
    if not repos_path.exists():
        print("repo path does not exist")
        return []
    
    for item in repos_path.iterdir():
        if item.is_dir():
            try:
                repo = git.Repo(item)
                
                if repo.bare:
                    repo_info = {
                        "name": item.name,
                        "path": str(item.absolute()),
                        "description": "",
                        "last_updated": None
                    }
                    
                    desc_file = item / "description"
                    if desc_file.exists():
                        try:
                            desc = desc_file.read_text().strip()
                            if not desc.startswith("Unnamed"):
                                repo_info["description"] = desc
                            else:
                                repo_info["description"] = "no description"
                        except:
                            pass
                    
                    try:
                        latest_commit = repo.head.commit
                        repo_info["last_updated"] = latest_commit.committed_datetime
                    except:
                        pass
                    
                    repos.append(repo_info)
            except Exception as e:
                print(f"error: {e}")
                pass
    
    return repos

def get_readme(repo_path=None):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return None
        
        head = repo.head.commit
        
        readme_names = ['README.md', 'README'] # there might be more...
        
        for readme_name in readme_names:
            try:
                blob = head.tree / readme_name
                return blob.data_stream.read().decode('utf-8')
            except KeyError:
                continue
        
        return None
        
    except Exception as e:
        print(f"error reading readme: {e}")
        return None

def get_commits(repo_path=None, max_count=20, skip=0):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return []
        
        commits = []
        for commit in repo.iter_commits('HEAD', max_count=max_count, skip=skip):
            commits.append({
                "hexsha": commit.hexsha,
                "author": commit.author.name,
                "date": commit.committed_datetime,
                "message": commit.message.strip()
            })
        
        return commits
        
    except Exception as e:
        print(f"error reading commits: {e}")
        return []
    
def get_commit(repo_path=None, commit_hash=None):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return None
        
        commit = repo.commit(commit_hash)

        if commit.parents:
            parent = commit.parents[0]
            diffs = parent.diff(commit, create_patch=True)
        else:
            # initial commit, no parents to compare to
            diffs = commit.diff(git.NULL_TREE, create_patch=True)
        
        return {
            "commit": commit,
            "diffs": diffs
        }
        
    except Exception as e:
        print(f"error reading commit: {e}")
        return None
    
def get_refs(repo_path=None):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return {"branches": [], "tags": []}
        
        branches = []
        tags = []
        
        # branches
        for head in repo.heads:
            branches.append({
                "name": head.name,
                "commit": head.commit.hexsha,
                "date": head.commit.committed_datetime,
                "message": head.commit.message.strip()
            })
        
        # tags
        for tag in repo.tags:
            tag_commit = tag.commit
            tags.append({
                "name": tag.name,
                "commit": tag_commit.hexsha,
                "date": tag_commit.committed_datetime,
                "message": tag_commit.message.strip()
            })
        
        return {"branches": branches, "tags": tags}
        
    except Exception as e:
        print(f"error reading refs: {e}")
        return {"branches": [], "tags": []}

def get_tree(repo_path=None, tree_path="", ref="HEAD"):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return None
        
        commit = repo.commit(ref)
        tree = commit.tree
        
        if tree_path:
            try:
                tree = tree / tree_path
            except KeyError:
                return None
        
        entries = []
        for item in tree:
            item_info = {
                "name": item.name,
                "type": item.type,  # blob or tree
                "path": item.path,
                "size": item.size if item.type == 'blob' else None
            }
            entries.append(item_info)

        # dirs -> files (all alphabetically)
        entries.sort(key=lambda x: (x['type'] != 'tree', x['name'].lower()))
        
        return {
            "entries": entries,
            "path": tree_path,
            "is_tree": tree.type == 'tree'
        }
        
    except Exception as e:
        print(f"error reading tree: {e}")
        return None