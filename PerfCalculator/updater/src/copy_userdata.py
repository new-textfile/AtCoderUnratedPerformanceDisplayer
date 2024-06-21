import json
import os
import shutil
from lib import path
from lib.type import UserResult
from typing import List, Dict, Set

def erase_oldfiles():
    print("[ACUPD-Updater(erase_oldfiles)] start")

    username_changes: Dict[str, str]
    with open(path.username_changes, "r") as f:
        username_changes = json.load(f)

    #旧ユーザー名のファイルの情報を消して保存する
    for old_user_name in username_changes.keys():
        if os.path.exists(path.userperfs_folder + old_user_name + ".json"):
            with open(path.new_userperfs_folder + old_user_name + ".json", "w") as f:
                json.dump({},f,indent=4)
        
        with open(path.new_useraperfs_folder + old_user_name + ".json", "w") as f:
            json.dump({},f,indent=4)

        with open(path.new_userinnerperfs_folder + old_user_name + ".json", "w") as f:
            json.dump({},f,indent=4)
    
    print("[ACUPD-Updater(erase_oldfiles)] finished")


def rename_files():
    print("[ACUPD-Updater(rename_files)] start")

    username_changes: Dict[str, str]
    with open(path.username_changes, "r") as f:
        username_changes = json.load(f)

    #旧ユーザー名のファイルの名前を新ユーザー名に変えて保存
    for old_user_name, new_user_name in username_changes.items():
        if os.path.exists(path.userperfs_folder + old_user_name + ".json"):
            shutil.copyfile(path.userperfs_folder + old_user_name + ".json", path.new_userperfs_folder + new_user_name + ".json")
        
        if os.path.exists(path.useraperfs_folder + old_user_name + ".json"):
            shutil.copyfile(path.useraperfs_folder + old_user_name + ".json", path.new_useraperfs_folder + new_user_name + ".json")
        
        if os.path.exists(path.userinnerperfs_folder + old_user_name + ".json"):
            shutil.copyfile(path.userinnerperfs_folder + old_user_name + ".json", path.new_userinnerperfs_folder + new_user_name + ".json")
    
    print("[ACUPD-Updater(rename_files)] end")


def copy_userdata() -> None:
    
    contest_name:str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    username_changes: Dict[str,str]
    with open(path.username_changes, "r") as f:
        username_changes = json.load(f)
    
    print("[ACUPD-Updater(copy_userdata)]start")

    changed_usernames: Set[str] = set(username_changes.values())
    for user_result in contest_result:
        username = user_result["UserScreenName"]

        #名前の変更を行ったユーザーのファイルは既にコピー済みなので飛ばす
        if username in changed_usernames: continue 
        
        if os.path.exists(path.userperfs_folder + username + ".json"):
            shutil.copyfile(path.userperfs_folder + username + ".json", path.new_userperfs_folder + username + ".json")
        
        if os.path.exists(path.useraperfs_folder + username + ".json"):
            shutil.copyfile(path.useraperfs_folder + username + ".json", path.new_useraperfs_folder + username + ".json") 
        
        if os.path.exists(path.userinnerperfs_folder + username + ".json"):
            shutil.copyfile(path.userinnerperfs_folder + username + ".json", path.new_userinnerperfs_folder + username + ".json")        

    print("[ACUPD-Updater(copy_userdata)] finished")



def prepare_userdata():
    erase_oldfiles()
    rename_files()
    copy_userdata()
