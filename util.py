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
                            if not desc.startswith("Unnamed") and not desc == "":
                                repo_info["description"] = desc
                            else:
                                repo_info["description"] = "-"
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

def get_readme(repo_path=None, ref='HEAD'):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return None
        
        try:
            commit = repo.commit(ref)
        except:
            # sometimes HEAD is empty, if so try the next ref, if still fails, give up
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
                commit = repo.commit(ref)
            else:
                raise
        
        readme_names = ['README.md', 'README'] # there might be more...
        
        for readme_name in readme_names:
            try:
                blob = commit.tree / readme_name
                return blob.data_stream.read().decode('utf-8')
            except KeyError:
                continue
        
        return None
        
    except Exception as e:
        print(f"error reading readme: {e}")
        return None

def get_commits(repo_path=None, max_count=20, skip=0, ref='HEAD'):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return []
        
        try:
            list(repo.iter_commits(ref, max_count=1))
        except:
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
            else:
                raise
        
        commits = []
        for commit in repo.iter_commits(ref, max_count=max_count, skip=skip):
            # lazily calculate stats with lib
            insertions = 0
            deletions = 0
            files_changed = 0
            
            try:
                stats = commit.stats.total
                insertions = stats.get('insertions', 0)
                deletions = stats.get('deletions', 0)
                files_changed = stats.get('files', 0)
            except Exception as e:
                print(f"error calculating stats for commit {commit.hexsha}: {e}")
            
            commits.append({
                "hexsha": commit.hexsha,
                "author": commit.author.name,
                "date": commit.committed_datetime,
                "message": commit.message.strip(),
                "files_changed": files_changed,
                "insertions": insertions,
                "deletions": deletions
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
        
        try:
            commit = repo.commit(ref)
        except:
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
                commit = repo.commit(ref)
            else:
                raise
        
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

def get_blob(repo_path=None, blob_path="", ref="HEAD"):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare:
            return None
        
        try:
            commit = repo.commit(ref)
        except:
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
                commit = repo.commit(ref)
            else:
                raise
        
        try:
            blob = commit.tree / blob_path
            
            if blob.type != 'blob':
                return None
            
            # try to read as text, if fails it's binary
            try:
                content = blob.data_stream.read().decode('utf-8')
                is_binary = False
            except UnicodeDecodeError:
                content = blob.data_stream.read()
                is_binary = True
            
            return {
                "name": blob.name,
                "path": blob_path,
                "size": blob.size,
                "content": content,
                "is_binary": is_binary,
                "hexsha": blob.hexsha
            }
        except KeyError:
            return None
        
    except Exception as e:
        print(f"error reading blob: {e}")
        return None
    
def create_bare_repo(repo_path, name, description=""):
    try:
        repo_path = Path(repo_path)
        new_repo_path = repo_path / name
        
        if new_repo_path.exists():
            return {
                "success": False,
                "message": f"repo '{name}' already exists"
            }
        
        repo = git.Repo.init(new_repo_path, bare=True)
        
        if description:
            desc_file = new_repo_path / "description"
            desc_file.write_text(description)
        
        return {
            "success": True,
            "message": f"successfully created bare repository '{name}'",
            "path": str(new_repo_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"error creating repository: {str(e)}"
        }

def search_commits(repo_path=None, query="", ref='HEAD'):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare or not query:
            return []
        
        try:
            list(repo.iter_commits(ref, max_count=1))
        except:
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
            else:
                raise
        
        results = []
        # maybe not wise to check all commits, but its problem for later (TODO)
        for commit in repo.iter_commits(ref):
            # search in commit message and author, searchin code 
            # reference for later https://github.blog/engineering/architecture-optimization/the-technology-behind-githubs-new-code-search/
            if (query.lower() in commit.message.lower() or 
                query.lower() in commit.author.name.lower()):
                results.append({
                    "hexsha": commit.hexsha,
                    "author": commit.author.name,
                    "date": commit.committed_datetime,
                    "message": commit.message.strip()
                })
                
        return results
        
    except Exception as e:
        print(f"error searching commits: {e}")
        return []
    
def search_files(repo_path=None, query="", ref="HEAD"):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare or not query:
            return []
        
        try:
            commit = repo.commit(ref)
        except:
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
                commit = repo.commit(ref)
            else:
                raise
        
        results = []
        
        # recursive tree traversal, also pieces together full paths for files
        # still very fast so no indexing for now
        def traverse_tree(tree, current_path=""):
            for item in tree:
                full_path = f"{current_path}/{item.name}" if current_path else item.name
                if query.lower() in item.name.lower():
                    results.append({
                        "name": item.name,
                        "path": full_path,
                        "type": item.type,
                        "size": item.size if item.type == 'blob' else None
                    })
                if item.type == 'tree':
                    traverse_tree(item, full_path)
        
        traverse_tree(commit.tree)
        
        return results
        
    except Exception as e:
        print(f"error searching files: {e}")
        return []
    
def search_code(repo_path=None, query="", ref="HEAD"):
    try:
        repo = git.Repo(repo_path)
        
        if not repo.bare or not query:
            return []
        
        try:
            commit = repo.commit(ref)
        except:
            if ref == "HEAD" and repo.heads:
                ref = repo.heads[0].name
                commit = repo.commit(ref)
            else:
                raise
        
        results = []
        
        # recursive tree traversal to search file contents, not even thinking about optimizations
        def traverse_tree(tree, current_path=""):
            for item in tree:
                full_path = f"{current_path}/{item.name}" if current_path else item.name
                if item.type == 'blob':
                    try:
                        # only search text files, skip binary files by exception
                        blob_content = item.data_stream.read().decode('utf-8', errors='ignore')
                        if query.lower() in blob_content.lower():
                            # find the line numbers where the query appears
                            lines = blob_content.split('\n')
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if query.lower() in line.lower():
                                    matching_lines.append({
                                        'line_number': i,
                                        'content': line.strip()
                                    })
                            
                            results.append({
                                "name": item.name,
                                "path": full_path,
                                "type": item.type,
                                "size": item.size,
                                "matching_lines": matching_lines 
                            })
                    except UnicodeDecodeError:
                        # skip binary 
                        pass
                elif item.type == 'tree':
                    traverse_tree(item, full_path)
        
        traverse_tree(commit.tree)
        
        return results
        
    except Exception as e:
        print(f"error searching code: {e}")
        return []

def set_repo_description(repo_path, description):
    try:
        repo_path = Path(repo_path)
        desc_file = repo_path / "description"
        desc_file.write_text(description)
        return True
    except Exception as e:
        print(f"error setting description: {e}")
        return False
