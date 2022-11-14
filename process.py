import json

with open("forks.json") as f:
    forks = json.load(f)

def get_content(repo, pred):
    return list(pred(lambda a: a["name"] == pred, repo["content"]))[0]