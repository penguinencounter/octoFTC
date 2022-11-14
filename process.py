import json
import shlex
import shutil
import subprocess
import logging

with open("forks.json") as f:
    forks = json.load(f)


def get_content(repo, pred):
    logging.info(f"Cloning {repo}...")
    subprocess.check_output(shlex.split(f"gh repo clone {repo} staging-target -- --depth 1"))  # clone the repo, only the latest commit


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    shutil.rmtree("staging-target", ignore_errors=True)
    get_content(forks[0], lambda: True)
