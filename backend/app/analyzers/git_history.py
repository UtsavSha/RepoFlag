from git import Repo
from typing import Dict, Any


def analyze_git_history(repo_path: str) -> Dict[str, Any]:
    print(f"Analyzing Git history intelligence for {repo_path}...")
    repo = None
    try:
        repo = Repo(repo_path)
        commits = list(repo.iter_commits('HEAD'))

        authors = set()
        file_changes = {}

        for commit in commits:
            authors.add(commit.author.email)
            for file in commit.stats.files:
                file_changes[file] = file_changes.get(file, 0) + 1

        hotspots = sorted(file_changes.items(),
                          key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_commits": len(commits),
            "unique_authors": len(authors),
            "hotspots": [{"file": f, "changes": c} for f, c in hotspots]
        }

    except Exception as e:
        print(f"Error analyzing git history: {e}")
        return {"total_commits": 0, "unique_authors": 0, "hotspots": []}
    finally:
        # Crucial for Windows: Release the file lock on the .git folder
        if repo:
            repo.close()
