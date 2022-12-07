import logging
import os
import json
from github import Github, InputGitTreeElement
from ..ACUPDlib import path
from ..ACUPDlib.type import UserResult
from typing import List

def update(usernamelist: List[str], commitmsgs: List[str], startidx:int=0, endidx:int=-1) -> None:
    if startidx >= len(usernamelist): return
    if endidx == -1: endidx = len(usernamelist)

    g = Github(os.environ["GITHUB_REPOSITORY_ACCESS_TOKEN"],timeout=300)
    repos = [g.get_repo("new-textfile/" + _) for _ in ["AtCoderUnratedPerformances", "ac_contest_results"]]
    refs = [repo.get_git_ref("heads/master") for repo in repos]
    commits = [repos[_].get_commit(refs[_].object.sha).commit for _ in range(2)]
    trees = [repos[_].get_git_tree(commits[_].sha) for _ in range(2)]

    elementlists: List[List[InputGitTreeElement]] = [[] for _ in range(2)]
    for username in usernamelist[startidx:min(endidx,len(usernamelist))]:
        if os.path.exists(path.new_userperfs_folder + username + ".json"):
            with open(path.new_userperfs_folder + username + ".json", "r") as f: 
                element = InputGitTreeElement("userperfs/" + username + ".json", "100644", "blob", f.read())
                elementlists[0].append(element)

        if os.path.exists(path.new_userinnerperfs_folder + username + ".json"):
            with open(path.new_userinnerperfs_folder + username + ".json", "r") as f: 
                element = InputGitTreeElement("userinnerperfs/" + username + ".json", "100644", "blob", f.read())
                elementlists[1].append(element)
                
        if os.path.exists(path.new_useraperfs_folder + username + ".json"):
            with open(path.new_useraperfs_folder + username + ".json", "r") as f: 
                element = InputGitTreeElement("useraperfs/" + username + ".json", "100644", "blob", f.read())
                elementlists[1].append(element)

    #まとめてtreeを作るとtimeoutするので, 複数回に分けて作成する
    UPDATE_RANGE = 20
    for i in range(2):
        if len(elementlists[i]) > 0:
            for j in range(0,len(elementlists[i]),UPDATE_RANGE):
                trees[i] = repos[i].create_git_tree(elementlists[i][j:j+UPDATE_RANGE], trees[i])
            new_commit = repos[i].create_git_commit(commitmsgs[i], trees[i], [commits[i]])
            refs[i].edit(new_commit.sha)


def update_renamed_users() -> None:
    logging.info("[ACUPD-Updater(update-repository) <renamed-users> uploading...")

    renamed_users:List[str]
    with open(path.renamed_users, "r") as f:
        renamed_users = json.load(f)

    contest_name:str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    if len(renamed_users) != 0: update(renamed_users, ["rename files(" + contest_name + ")"]*2)

    logging.info("[ACUPD-Updater(update-repository) <renamed-users> finished")


def update_contestants(startidx:int, endidx:int) -> None:

    contest_name: str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    logging.info("[ACUPD-Updater(update-repository) <"+ str(startidx) + "-" + str(endidx) + "> uploading...")

    commitmsgs = ["update " + _ + "(" + contest_name + ") <" + str(startidx) + "-" + str(endidx) + ">"  for _ in ["userperfs", "useraperfs and userinnerperfs"]]
    update([user_result.get("UserScreenName") for user_result in contest_result], commitmsgs, startidx, endidx)
    
    logging.info("[ACUPD-Updater(update-repository) <"+ str(startidx) + "-" + str(endidx) + "> finished...")


def update_new_contest_info() -> None:
    logging.info("[ACUPD-Updater(update-repository) <new-contest-info> uploading...")

    g = Github(os.environ["GITHUB_REPOSITORY_ACCESS_TOKEN"],timeout=300)
    repo = g.get_repo("new-textfile/ac_contest_results")
    ref = repo.get_git_ref("heads/master")
    commit = repo.get_commit(ref.object.sha).commit
    tree = repo.get_git_tree(commit.sha)

    contest_name:str
    with open(path.new_contests,"r") as f:
        contest_name = json.load(f)[0]

    elementlist: List[InputGitTreeElement] = []
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        element = InputGitTreeElement("results/" + contest_name + ".json", "100644", "blob", f.read())
        elementlist.append(element)
        
    with open(path.new_fetched_contests, "r") as f:
        element = InputGitTreeElement("fetched_contests.json", "100644", "blob", f.read())
        elementlist.append(element)

    with open(path.new_fetched_contests_info, "r") as f:
        element = InputGitTreeElement("fetched_contests_info.json", "100644", "blob", f.read())
        elementlist.append(element)

    with open(path.new_defaultaperfs, "r") as f:
        element = InputGitTreeElement("default_aperfs.json", "100644", "blob", f.read())
        elementlist.append(element)

    tree = repo.create_git_tree(elementlist, tree)
    new_commit = repo.create_git_commit("update contest info (" + contest_name + ")", tree, [commit])
    ref.edit(new_commit.sha)

    logging.info("[ACUPD-Updater(update-repository) <new-contest-info> finished")


def main(name:str) -> None:

    if name.split("@")[0] == "renamed_users":
        update_renamed_users()
    
    elif name.split("@")[0] == "new_contest_info":
        update_new_contest_info()

    elif name.split("@")[0] == "contestants":
        startidx = int(name.split("@")[1].split("-")[0])
        endidx = int(name.split("@")[1].split("-")[1])
        update_contestants(startidx,endidx)
