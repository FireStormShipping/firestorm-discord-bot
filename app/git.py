import logging
import shutil
from pathlib import Path

import pygit2
import requests

logger = logging.getLogger("firestorm_bot")

DATASET_BRANCH = "dataset-updates"

class GitCallbacks(pygit2.RemoteCallbacks):
    def __init__(self, user=None, token=None, pub_key=None, priv_key=None, passphrase=None):
        self.user = user
        self.token = token
        self.pub_key = pub_key
        self.priv_key = priv_key
        self.passphrase = passphrase

    def credentials(self, url, username_from_url, allowed_types):
        # if allowed_types & pygit2.enums.CredentialType.USERNAME:
        #     return pygit2.Username(self.user)
        # elif allowed_types & pygit2.enums.CredentialType.SSH_KEY:
        #     return pygit2.Keypair(username_from_url, self.pub_key, self.priv_key, self.passphrase)
        if allowed_types & pygit2.enums.CredentialType.USERPASS_PLAINTEXT:
            return pygit2.UserPass(self.user, self.token)
        return None

class GitWrapper:
    def __init__(self,
        git_user: str,
        git_token: str,
        upstream_repo: str,
        forked_repo: str,
        local_path: str
    ):
        self.git_user = git_user
        self.git_token = git_token
        # Format: <username>/<repo_name>
        self.upstream_repo = upstream_repo
        # Format: <username>/<repo_name>
        self.forked_repo = forked_repo
        # Local path to the forked git repo.
        self.local_path = Path(local_path)

    def get_local_path(self) -> str:
        return str(self.local_path)

    def push_to_remote(
        self,
        repo: pygit2.Repository,
        remote_name: str = "origin"
    ) -> None | Exception:
        """Sync the local changes to to the remote repo."""
        repo.remotes[remote_name].push(
            [f"+refs/heads/{DATASET_BRANCH}"],
            callbacks=GitCallbacks(user=self.git_user, token=self.git_token)
        )

    def sync_forked_repo_with_upstream(self) -> str | Exception:
        """
        Sync the main branch of the forked repo with the upstream,
        to ensure it has the latest changes.
        """

        headers = {
            "Authorization": f"Bearer {self.git_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10"
        }

        data = {
            "branch": "main",
        }

        response = requests.post(
            f"https://api.github.com/repos/{self.forked_repo}/merge-upstream",
            headers=headers,
            json=data,
            timeout=5
        )

        if response.status_code != 200:
            raise RuntimeError(str(response.json()))
        resp = response.json()
        return resp["message"]

    def clone_fresh(
        self,
        branch: str = "main",
        depth: int = 1
    ) -> pygit2.Repository:
        """
        1. Checks whether the repo exists locally.
        2. If it does, remove it first.
        3. Now clone or re-clone the repo.

        :param branch: Branch to clone, defaults to main.
        :param depth: How many commits to clone, default to only the head.
        """
        if self.local_path.exists():
            shutil.rmtree(self.local_path)

        return pygit2.clone_repository(
            f"https://github.com/{self.forked_repo}.git",
            str(self.local_path),
            checkout_branch=branch,
            depth=depth,
        )

    def commit_changes(self, repo: pygit2.Repository) -> None:
        # Create a new branch for our changes
        last_commit = repo.revparse_single("HEAD")
        _new_branch = repo.branches.local.create(DATASET_BRANCH, last_commit)
        repo.checkout(repo.branches.local[DATASET_BRANCH])

        # Commit the changes.
        index = repo.index
        index.add_all()
        ref = repo.head.name
        parents = [ repo.head.target ]
        author = pygit2.Signature(
            'firestorm-automation',
            'firestorm-automation@firestorm.love'
        )
        tree = index.write_tree()
        message = "Update dataset."
        commit = repo.create_commit(ref, author, author, message, tree, parents)
        logger.info(f"[GitWrapper] Changes Committed: {commit}")

    def make_pull_request(self) -> str | Exception:
        """
        Makes a pull request on Github.
        :return: PR URL if success, Exception otherwise.
        """
        headers = {
            "Authorization": f"Bearer {self.git_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # The repo or branch to sync to the upstream.
        # same repo: set the head as <branch>
        # forked repo: set the head as <forkUser>:<branch>.
        data = {
            "title": "Sync Dataset",
            "head": f"{self.git_user}:{DATASET_BRANCH}",
            "base": "main", # Assume that prod is main branch.
            "body": "Updating the dataset to sync with the DB."
        }

        response = requests.post(
            f"https://api.github.com/repos/{self.upstream_repo}/pulls",
            headers=headers,
            json=data,
            timeout=5
        )

        if response.status_code != 201:
            raise RuntimeError(str(response.json()))
        resp = response.json()
        return resp["html_url"]
