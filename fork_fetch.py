# Get a list of forks of FIRST-Tech-Challenge/FTCRobotController
# Assume GitHub CLI is installed.
import shlex
import subprocess
import json
import logging


def get_forks(pages: int = 1, silent: bool = False):
    out = []
    for x in range(pages):
        if not silent:
            logging.info(f"Request forks: page {x + 1} of {pages}")
        r = json.loads(subprocess.check_output(
            shlex.split(f"gh api repos/FIRST-Tech-Challenge/FTCRobotController/forks?per_page=100&page={x + 1}")
        ))
        if len(r) == 0:
            if not silent:
                logging.info(f"Reached end, stopping early")
            break
        out += r
    return out


def run(silent: bool = False):
    forks = get_forks(3, silent=silent)
    if not silent:
        logging.info(f'collected {len(forks)} forks total')
    with open('forks.json', 'w') as f:
        json.dump(list(map(lambda a: a["full_name"], forks)), f, indent=4)
    return forks


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()
