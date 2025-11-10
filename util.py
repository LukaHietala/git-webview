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
                        "description": ""
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
                    
                    repos.append(repo_info)
            except Exception as e:
                print(f"error: {e}")
                pass
    
    return repos

