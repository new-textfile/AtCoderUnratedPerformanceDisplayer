import os
import glob
import shutil
from lib import path

#コンテスト参加者(+名前の変更を行ったユーザー)の内部レート・内部パフォーマンス・パフォーマンスのファイルを更新
def update_contestants() -> None:
      
    print("[ACUPD-Updater(update_contestants)] update_contestants start")
    
    for filepath in glob.glob(path.new_useraperfs_folder + "*.json"):
        shutil.move(filepath, path.useraperfs_folder + os.path.basename(filepath))

    for filepath in glob.glob(path.new_userperfs_folder + "*.json"):
        shutil.move(filepath, path.userperfs_folder + os.path.basename(filepath))

    for filepath in glob.glob(path.new_userinnerperfs_folder + "*.json"):
        shutil.move(filepath, path.userinnerperfs_folder + os.path.basename(filepath))

    print("[ACUPD-Updater(update_contestants)] update_contestants finished")


#コンテスト結果(results)のファイルを更新
def move_resultfiles() -> None:
    for filepath in glob.glob(path.new_results_folder + "*.json"):
        shutil.move(filepath, path.results_folder + os.path.basename(filepath))
        
    print("[ACUPD-Updater(move_resultfiles)] move_resultfiles finished")


#取得済みコンテスト一覧を更新
def update_fetched_contests() -> None:
    if os.path.exists(path.new_fetched_contests):
        shutil.move(path.new_fetched_contests, path.fetched_contests)
    
    if os.path.exists(path.new_fetched_contests_info):
        shutil.move(path.new_fetched_contests_info, path.fetched_contests_info)
    
    print("[ACUPD-Updater(update_fetched_contests)] update_fetched_contests finished")


#デフォルト内部レート一覧を更新
def update_defaultaperfs() -> None:
    if os.path.exists(path.new_defaultaperfs):
        shutil.move(path.new_defaultaperfs, path.defaultaperfs)
    
    print("[ACUPD-Updater(update_defaultaperfs)] update_defaultaperfs finished")


#一時ファイルを削除
def delete_tempfiles() -> None:
    
    file_paths = []
    file_paths.append(path.new_fetched_contests)
    file_paths.append(path.new_fetched_contests_info)
    file_paths.append(path.new_defaultaperfs)
    file_paths.append(path.new_contests)
    file_paths.append(path.calculate_tempdata)
    file_paths.append(path.renamed_users)
    file_paths.append(path.username_changes)
    file_paths.append(path.fetch_tempdata)
    file_paths.append(path.upload_tempdata)
    file_paths.append(path.update_status)

    for file_path in file_paths:
        if os.path.exists(file_path): os.remove(file_path)

    folder_paths = []
    folder_paths.append(path.new_results_folder)
    folder_paths.append(path.new_temp_results_folder)
    folder_paths.append(path.new_useraperfs_folder)
    folder_paths.append(path.new_userperfs_folder)
    folder_paths.append(path.new_userinnerperfs_folder)

    for folder_path in folder_paths:
        for file_path in glob.glob(folder_path + "*.*"):
            os.remove(file_path)
    
    print("[ACUPD-Updater(delete_tempfiles)] delete_tempfiles finished")

def update_files():
    update_contestants()
    move_resultfiles()
    update_fetched_contests()
    update_defaultaperfs()
    delete_tempfiles()
    