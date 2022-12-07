import logging

import json
import shutil
import os
from ..ACUPDlib import path
from ..ACUPDlib.type import UserResult
from typing import List, Set, Dict

def main(name:str) -> None:
    logging.info("[ACUPD-Updater(correct_username_changes)] loading start")

    #fetched_contestsを取得
    fetched_contests: List[str]
    with open(path.fetched_contests, "r") as f:
        fetched_contests = json.load(f)["contests"]

    renamed_users: Set[str] = set()

    username_changes: Dict[str, str] = {} # users = { 変更前の名前1 : 変更後の名前1 , ...} 
    for contest_name in fetched_contests:
        
        #前回取得したcontest_result
        old_contest_result: List[UserResult]
        with open(path.results_folder + contest_name + ".json", "r") as f:
            old_contest_result = json.load(f)

        #今回取得したcontest_result
        new_contest_result: List[UserResult]
        with open(path.new_results_folder + contest_name + ".json", "r") as f:
            new_contest_result = json.load(f)

        #ユーザー名変更を検出
        for i in range(len(old_contest_result)):
            old_user_name = old_contest_result[i]["UserScreenName"]
            new_user_name = new_contest_result[i]["UserScreenName"]

            if old_user_name != new_user_name:
                username_changes[old_user_name] = new_user_name
                renamed_users.add(old_user_name)
                renamed_users.add(new_user_name)

    logging.info("[ACUPD-Updater(correct_username_changes)] loading finished")

    #旧ユーザー名のファイルの情報を消して別名で保存する
    for old_user_name in username_changes.keys():
        if os.path.exists(path.userperfs_folder + old_user_name + ".json"):
            with open(path.new_userperfs_folder + old_user_name + ".json", "w") as f:
                json.dump({},f,indent=4)
        
        with open(path.new_useraperfs_folder + old_user_name + ".json", "w") as f:
            json.dump({},f,indent=4)

        with open(path.new_userinnerperfs_folder + old_user_name + ".json", "w") as f:
            json.dump({},f,indent=4)

    #旧ユーザー名のファイルの名前を新ユーザー名に変えて保存
    for old_user_name, new_user_name in username_changes.items():
        if os.path.exists(path.userperfs_folder + old_user_name + ".json"):
            shutil.copyfile(path.userperfs_folder + old_user_name + ".json", path.new_userperfs_folder + new_user_name + ".json")
        shutil.copyfile(path.useraperfs_folder + old_user_name + ".json", path.new_useraperfs_folder + new_user_name + ".json")
        shutil.copyfile(path.userinnerperfs_folder + old_user_name + ".json", path.new_userinnerperfs_folder + new_user_name + ".json")

    #変更に関連するユーザー名の一覧を保存
    with open(path.renamed_users, "w") as f:
        json.dump(list(renamed_users), f, indent=4)
    
    #ユーザー名の変化を保存
    with open(path.username_changes, "w") as f:
        json.dump(username_changes, f, indent=4)

    logging.info("[ACUPD-Updater(correct_username_changes)] correct finished")
