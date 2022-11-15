import base64
import copy
import json
import logging
import shlex
import subprocess
import threading
import time
import typing


class StateError(RuntimeError):
    pass


def keep(d: dict, keys: list):
    return {k: d[k] for k in keys if k in d}


class RepoView:
    """
    Represents a GitHub repository.
    """

    def __init__(self, repo: str, root_items: list):
        self.repo = repo
        self.refs = []
        for item in root_items:
            a = keep(item, ["path", "type", "sha", "size", "git_url"])
            a["url"] = a["git_url"]
            del a["git_url"]
            self.refs.append(a)
        self._resolved = False
        self._root_items = root_items
        logging.info(f"Created RepoView:")
        counter = 0
        for ref in self.refs:
            path, typ, sha = ref["path"], ref["type"], ref["sha"]
            counter += 1
            logging.info(f"  {path} ({typ} {sha[:8]}...)")
            if counter >= 5:
                logging.info(f"  ... +more")
                break
        logging.info("Resolving...")
        self._resolve()

    def _resolve(self):
        """
        Resolves the repository.
        """
        if self._resolved:
            raise StateError("RepoView already resolved")
        build = copy.deepcopy(self.refs)
        for ref in self.refs:
            path, typ, sha = ref["path"], ref["type"], ref["sha"]
            if typ in ["dir", "tree"]:
                logging.info("  resolve dir " + path)
                tree = json.loads(subprocess.check_output(
                    shlex.split(f"gh api {GH_EXTRA} /repos/{self.repo}/git/trees/{sha}?recursive=1")))["tree"]
                logging.info(f"   ... {len(tree)} items to add")
                trimmed = []
                for item in tree:
                    a = keep(item, ["path", "type", "sha", "size", "url"])
                    a["path"] = path + "/" + a["path"]
                    trimmed.append(a)
                build += trimmed
                logging.info(f"   -> {len(tree)} trimmed + added")
        logging.info(f"Updating...")
        self.refs = build
        logging.info(f"  -> new total: {len(self.refs)} items")
        self._resolved = True


GH_EXTRA = '-H "Accept: application/vnd.github+json"'

with open("forks.json") as f:
    forks = json.load(f)


def get_content(repo: str, pred: typing.Callable[[RepoView], bool]):
    logging.info(f"Getting map of {repo}...")
    logging.info(f"  Get root of {repo}...")
    root = json.loads(subprocess.check_output(shlex.split(f"gh api {GH_EXTRA} /repos/{repo}/contents/")))
    logging.info(f"  -> done ({len(root)} items)")
    view = RepoView(repo, root)
    logging.info(f"Executing predicate...")
    result = pred(view)
    return result


def get_file_blob(url: str):
    """
    Utility function to get the blob of a file.
    :param url: provided
    :return: content of the file
    """
    logging.info(f"  Get blob of {url}...")
    blob = json.loads(subprocess.check_output(shlex.split(f"gh api {GH_EXTRA} {url}")))
    return base64.b64decode(blob["content"])


def example_predicate(view: RepoView) -> bool:
    # find all repos with "com.acmerobotics.roadrunner" in one of their Gradle files
    for ref in view.refs:
        path = ref["path"]
        if path.endswith(".gradle"):
            blob = get_file_blob(ref["url"])
            if b"com.acmerobotics.roadrunner" in blob.lower():
                logging.info(f"{view.repo} uses RoadRunner:")
                logging.info(f"  -> found in {path}")
                return True
    return False


def make_batch(cook_count: int, targets: list, pred: typing.Callable[[RepoView], bool]):
    cooks = []
    matching = []
    targets = copy.deepcopy(targets)

    def cook():
        while len(targets) > 0:
            job = targets.pop()
            logging.info(f"Starting job for {job}...")
            try:
                if get_content(job, pred):
                    matching.append(job)
            except Exception as e:
                logging.error(f"Error while processing {job}: {e}")
            logging.info(f"Job for {job} done.")

    logging.info("Starting batch job...")
    for i in range(cook_count):
        t = threading.Thread(target=cook)
        t.start()
        cooks.append(t)

    while 1:
        alive = False
        for t in cooks:
            if t.is_alive():
                alive = True
                break
        if not alive:
            break
        else:
            logging.info(f"{len(targets)} jobs left...")
            time.sleep(1)

    return matching


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    coll = make_batch(3, forks, example_predicate)
    print(coll)
