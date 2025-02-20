import argparse
import os
from datetime import datetime, timedelta, timezone
from github import Github


def get_github_repo():
    """Retrieve GitHub repository using the provided token."""
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")  # Expected format: "user/repo"

    if not token:
        raise ValueError("Error: GITHUB_TOKEN environment variable is not set.")

    if not repo_name:
        raise ValueError("Error: GITHUB_REPOSITORY environment variable is not set.")

    github_client = Github(token)
    return github_client.get_repo(repo_name)


def get_cutoff_date(months: int) -> datetime:
    """Calculate the cutoff date for branch deletion based on inactivity."""
    return datetime.now(timezone.utc) - timedelta(days=months * 30)


def get_stale_branches(repo, cutoff_date, excluded_branches):
    """Retrieve branches that have been inactive beyond the cutoff date."""
    stale_branches = []

    for branch in repo.get_branches():
        if branch.name in excluded_branches:
            continue

        commit = repo.get_commit(branch.commit.sha)
        commit_date = commit.commit.author.date  # Already timezone-aware

        print(f"Checking branch '{branch.name}' | Last commit: {commit_date}")

        if commit_date <= cutoff_date:
            stale_branches.append(branch.name)

    return stale_branches


def delete_branches(repo, branches, dry_run: bool):
    """Delete branches if not in dry-run mode, otherwise print branches to be deleted."""
    if not branches:
        print("No branches meet the criteria for deletion.")
        return

    if dry_run:
        print("Dry-run mode: The following branches would be deleted:")
        for branch in branches:
            print(f"- {branch}")
    else:
        for branch in branches:
            repo.get_git_ref(f"heads/{branch}").delete()
            print(f"Deleted branch: {branch}")


def main(dry_run: bool, offset_months: int):
    """Main function to execute the branch cleanup process."""
    if offset_months < 6:
        print("Error: The minimum inactivity period required is 6 months.")
        return

    print(f"Running GitHub branch cleanup | Offset months: {offset_months}")

    repo = get_github_repo()
    excluded_branches = {repo.default_branch, "develop", "stage"}

    cutoff_date = get_cutoff_date(offset_months)
    print(f"Cutoff date: {cutoff_date}")

    stale_branches = get_stale_branches(repo, cutoff_date, excluded_branches)
    delete_branches(repo, stale_branches, dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete inactive branches from a GitHub repository.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the deletion process without making changes.")
    parser.add_argument("--months", type=int, default=6, help="Months of inactivity required before deletion.")
    
    args = parser.parse_args()
    main(args.dry_run, args.months)
