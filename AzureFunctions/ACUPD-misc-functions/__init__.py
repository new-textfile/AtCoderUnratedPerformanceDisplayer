import logging
import json
import glob
import os
import shutil
from ..ACUPDlib import path
from ..ACUPDlib.type import UserResult
from typing import List, Dict, Set

#Azure Durable Functions 実行用の一時ファイルを削除
def delete_tempfiles() -> None:
    
    if os.path.exists(path.new_fetched_contests): os.remove(path.new_fetched_contests)
    if os.path.exists(path.new_fetched_contests_info): os.remove(path.new_fetched_contests_info)
    if os.path.exists(path.new_defaultaperfs): os.remove(path.new_defaultaperfs)
    if os.path.exists(path.new_contests): os.remove(path.new_contests)
    if os.path.exists(path.calculate_tempdata): os.remove(path.calculate_tempdata)
    if os.path.exists(path.renamed_users): os.remove(path.renamed_users)
    if os.path.exists(path.username_changes): os.remove(path.username_changes)
    if os.path.exists(path.fetch_tempdata): os.remove(path.fetch_tempdata)

    for filepath in glob.glob(path.new_results_folder + "*.*"):
        os.remove(filepath)
    
    for filepath in glob.glob(path.new_temp_results_folder + "*.*"):
        os.remove(filepath)
    
    for filepath in glob.glob(path.new_useraperfs_folder + "*.*"):
        os.remove(filepath)
    
    for filepath in glob.glob(path.new_userperfs_folder + "*.*"):
        os.remove(filepath)

    for filepath in glob.glob(path.new_userinnerperfs_folder + "*.*"):
        os.remove(filepath)
    
    logging.info("[ACUPD-Updater(delete_tempfiles)] delete_tempfiles finished")
    

#Azure Durable Functions 実行用の一時ファイルを格納するためのフォルダを作成
def create_tempfolders() -> None:
    if not os.path.exists(path.tempdata_folder): os.mkdir(path.tempdata_folder)
    if not os.path.exists(path.new_results_folder): os.mkdir(path.new_results_folder)
    if not os.path.exists(path.new_temp_results_folder): os.mkdir(path.new_temp_results_folder)
    if not os.path.exists(path.new_userperfs_folder): os.mkdir(path.new_userperfs_folder)
    if not os.path.exists(path.new_userinnerperfs_folder): os.mkdir(path.new_userinnerperfs_folder)
    if not os.path.exists(path.new_useraperfs_folder): os.mkdir(path.new_useraperfs_folder)
    
    logging.info("[ACUPD-Updater(create_tempfolders)] create_tempfolders finished")


#コンテスト結果(results)のファイルを更新
def move_resultfiles() -> None:
    for filepath in glob.glob(path.new_results_folder + "*.json"):
        shutil.move(filepath, path.results_folder + os.path.basename(filepath))
        
    logging.info("[ACUPD-Updater(move_resultfiles)] move_resultfiles finished")


#取得済みコンテスト一覧を更新
def update_fetched_contests() -> None:
    if os.path.exists(path.new_fetched_contests):
        shutil.move(path.new_fetched_contests, path.fetched_contests)
    
    if os.path.exists(path.new_fetched_contests_info):
        shutil.move(path.new_fetched_contests_info, path.fetched_contests_info)
    
    logging.info("[ACUPD-Updater(update_fetched_contests)] update_fetched_contests finished")


#デフォルト内部レート一覧を更新
def update_defaultaperfs() -> None:
    if os.path.exists(path.new_defaultaperfs):
        shutil.move(path.new_defaultaperfs, path.defaultaperfs)
    
    logging.info("[ACUPD-Updater(update_defaultaperfs)] update_defaultaperfs finished")


#ユーザー名変更を行った人の内部レート・内部パフォーマンス・パフォーマンスのファイルを更新
def update_renamed_users() -> None:
    logging.info("[ACUPD-Updater(update_renamed_users)] update_renamed_users start")

    renamed_users: List[str]
    with open(path.renamed_users, "r") as f:
        renamed_users = json.load(f)

    for user_name in renamed_users:
        if os.path.exists(path.new_userperfs_folder + user_name + ".json"):
            shutil.move(path.new_userperfs_folder + user_name + ".json", path.userperfs_folder + user_name + ".json")
        shutil.move(path.new_useraperfs_folder + user_name + ".json", path.useraperfs_folder + user_name + ".json") 
        shutil.move(path.new_userinnerperfs_folder + user_name + ".json", path.userinnerperfs_folder + user_name + ".json")        

    logging.info("[ACUPD-Updater(update_renamed_users)] update_renamed_users finished")


#コンテスト参加者の内部レート・内部パフォーマンス・パフォーマンスのファイルを更新
def update_contestants(startidx:int, endidx:int) -> None:
    
    contest_name:str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)
    
    logging.info("[ACUPD-Updater(update_contestants)] <idx: " + str(startidx) + "-" + str(endidx) + "> update_contestants start")

    for user_result in contest_result[startidx:endidx]:
        user_name = user_result["UserScreenName"]
        
        if os.path.exists(path.new_userperfs_folder + user_name + ".json"):
            shutil.move(path.new_userperfs_folder + user_name + ".json", path.userperfs_folder + user_name + ".json")
        
        if os.path.exists(path.new_useraperfs_folder + user_name + ".json"):
            shutil.move(path.new_useraperfs_folder + user_name + ".json", path.useraperfs_folder + user_name + ".json") 
        
        if os.path.exists(path.new_userinnerperfs_folder + user_name + ".json"):
            shutil.move(path.new_userinnerperfs_folder + user_name + ".json", path.userinnerperfs_folder + user_name + ".json")        

    logging.info("[ACUPD-Updater(update_contestants)] <idx: " + str(startidx) + "-" + str(endidx) + "> update_contestants finished")


def copy_userdata(startidx:int, endidx:int) -> None:
    
    contest_name:str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    username_changes: Dict[str,str]
    with open(path.username_changes, "r") as f:
        username_changes = json.load(f)
    
    logging.info("[ACUPD-Updater(copy_userdata)] <idx: " + str(startidx) + "-" + str(endidx) + "> copy_userdata start")

    changed_usernames: Set[str] = set(username_changes.values())
    for user_result in contest_result[startidx:endidx]:
        username = user_result["UserScreenName"]

        #名前の変更を行ったユーザーのファイルは既にコピー済みなので飛ばす
        if username in changed_usernames: continue 
        
        if os.path.exists(path.userperfs_folder + username + ".json"):
            shutil.copyfile(path.userperfs_folder + username + ".json", path.new_userperfs_folder + username + ".json")
        
        shutil.copyfile(path.useraperfs_folder + username + ".json", path.new_useraperfs_folder + username + ".json") 
        shutil.copyfile(path.userinnerperfs_folder + username + ".json", path.new_userinnerperfs_folder + username + ".json")        

    logging.info("[ACUPD-Updater(copy_userdata)] <idx: " + str(startidx) + "-" + str(endidx) + "> copy_userdata finished")


def move_temp_results() -> None:

    for filepath in glob.glob(path.new_temp_results_folder + "*.json"):
        filename = os.path.basename(filepath)
        shutil.move(filepath, path.new_results_folder + filename)


def main(name: str) -> None:

    if name.split("@")[0] == "create_tempfolders":
        create_tempfolders()

    elif name.split("@")[0] == "delete_tempfiles":
        delete_tempfiles()

    elif name.split("@")[0] == "move_temp_results":
        move_temp_results()

    elif name.split("@")[0] == "update_results":
        move_resultfiles()

    elif name.split("@")[0] == "update_fetched_contests":
        update_fetched_contests()

    elif name.split("@")[0] == "update_defaultaperfs":
        update_defaultaperfs()

    elif name.split("@")[0] == "update_renamed_users":
        update_renamed_users()

    elif name.split("@")[0] == "update_contestants":
        startidx = int(name.split("@")[1].split("-")[0])
        endidx = int(name.split("@")[1].split("-")[1])
        update_contestants(startidx,endidx)

    elif name.split("@")[0] == "copy_userdata":
        startidx = int(name.split("@")[1].split("-")[0])
        endidx = int(name.split("@")[1].split("-")[1])
        copy_userdata(startidx,endidx)

