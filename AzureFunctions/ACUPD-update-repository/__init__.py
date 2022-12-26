import logging
import os
import json
from github import Github, InputGitTreeElement, GithubException
from ..ACUPDlib import path
from ..ACUPDlib.type import UserResult
from ..ACUPDlib.updatecheck import check_update_status
from typing import List, Dict

UPLOAD_UNFINISHED = 0
UPLOAD_HALF_FINISHED = 1
UPLOAD_FINISHED = 2


def upload(usernamelist: List[str], commitmsgs: List[str], upload_name:str, update_range:int, startidx:int=0, endidx:int=-1) -> None:
    if startidx >= len(usernamelist): return 
    if endidx == -1: endidx = len(usernamelist)

    #upload状況を確認して新たにuploadを行う必要があるかどうか判断
    update_status:int = UPLOAD_UNFINISHED
    if os.path.exists(path.upload_tempdata): 
        uploaded_check:Dict[str, int]
        with open(path.upload_tempdata, "r") as f:
            uploaded_check = json.load(f)
        
        update_status = uploaded_check.get(upload_name, UPLOAD_UNFINISHED)
        if update_status == UPLOAD_FINISHED: return

    github = Github(os.environ["GITHUB_REPOSITORY_ACCESS_TOKEN"],timeout=600)
    repos = [github.get_repo("new-textfile/" + _) for _ in ["AtCoderUnratedPerformances", "ac_contest_results"]]
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

    
    logging.info("[ACUPD-Updater(update_repository)] status=" + ("HALF_FINISHED" if update_status == UPLOAD_HALF_FINISHED else "UNFINISHED")  + ")")


    #まとめてtreeを作るとtimeoutするので, 複数回に分けて作成する
    #ただし, 要素を1個ずつtreeに追加していくと非常に時間がかかるので, ある個数ごとにまとめて追加する 
    for i in range(2):
        if i == 0 and update_status == UPLOAD_HALF_FINISHED: continue

        if len(elementlists[i]) > 0:
            while True:
                trees[i] = repos[i].get_git_tree(commits[i].sha)
                
                try:
                    for j in range(0,len(elementlists[i]),update_range):
                        trees[i] = repos[i].create_git_tree(elementlists[i][j:j+update_range], trees[i])
                    break

                except GithubException as e:
                    logging.info("[ACUPD-Updater(update_repository)] create git tree failed(range=" + str(update_range) + ")")
                    logging.info(e.data)

                    #upload状況を保存
                    upload_tempdata:Dict[str,int] = {}
                    if os.path.exists(path.upload_tempdata):
                        with open(path.upload_tempdata, "r") as f:
                            upload_tempdata = json.load(f)

                    upload_tempdata[upload_name] = UPLOAD_HALF_FINISHED if i == 1 else UPLOAD_UNFINISHED
                    
                    with open(path.upload_tempdata, "w") as f:
                        json.dump(upload_tempdata, f, indent=4)

                    return

            #commitを作成して反映させる
            logging.info("[ACUPD-Updater(update_repository)] commiting... (" + ["AtCoderUnratedPerformances", "ac_contest_results"][i] + ")")
            new_commit = repos[i].create_git_commit(commitmsgs[i], trees[i], [commits[i]])
            refs[i].edit(new_commit.sha)

    #upload状況を保存
    upload_tempdata:Dict[str,int] = {}
    if os.path.exists(path.upload_tempdata):
        with open(path.upload_tempdata, "r") as f:
            upload_tempdata = json.load(f)
    
    upload_tempdata[upload_name] = UPLOAD_FINISHED

    with open(path.upload_tempdata, "w") as f:
        json.dump(upload_tempdata, f, indent=4)


def update_renamed_users(update_range:int, upload_name:str) -> None:
    logging.info("[ACUPD-Updater(update-repository)] <renamed-users>" + "(" + str(update_range) +") uploading...")

    renamed_users:List[str]
    with open(path.renamed_users, "r") as f:
        renamed_users = json.load(f)

    contest_name:str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    if len(renamed_users) != 0: upload(renamed_users, ["rename files(" + contest_name + ")"]*2, upload_name, update_range)

    logging.info("[ACUPD-Updater(update-repository)] <renamed-users>" + "(" + str(update_range) +") finished")


def update_contestants(startidx:int, endidx:int, update_range:int, upload_name:str) -> None:

    contest_name: str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    logging.info("[ACUPD-Updater(update-repository) <"+ str(startidx) + "-" + str(endidx) + "> uploading...")

    commitmsgs = ["update " + _ + "(" + contest_name + ") <" + str(startidx) + "-" + str(endidx) + ">"  for _ in ["userperfs", "useraperfs and userinnerperfs"]]
    upload([user_result.get("UserScreenName") for user_result in contest_result], commitmsgs, upload_name, update_range, startidx, endidx)
    
    logging.info("[ACUPD-Updater(update-repository) <"+ str(startidx) + "-" + str(endidx) + "> finished...")


def upload_new_contest_info() -> None:
    logging.info("[ACUPD-Updater(update-repository) <new-contest-info> uploading...")

    github = Github(os.environ["GITHUB_REPOSITORY_ACCESS_TOKEN"],timeout=300)
    repo = github.get_repo("new-textfile/ac_contest_results")
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


def main(name:str) -> str:
    if not check_update_status(): return ""

    if name.split("@")[0] == "renamed_users":
        update_range = int(name.split("@")[1])
        update_renamed_users(update_range, name.split("@")[0])
    
    elif name.split("@")[0] == "new_contest_info":
        upload_new_contest_info()

    elif name.split("@")[0] == "contestants":
        update_range = int(name.split("@")[1])
        startidx = int(name.split("@")[2].split("-")[0])
        endidx = int(name.split("@")[2].split("-")[1])
        update_contestants(startidx, endidx, update_range, name.split("@")[0] + "@" + name.split("@")[2])

    return ""