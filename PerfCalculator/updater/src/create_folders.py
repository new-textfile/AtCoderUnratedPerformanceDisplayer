import os
from lib import path

def create_folders() -> None:

    folder_paths = []
    folder_paths.append(path.tempdata_folder)
    folder_paths.append(path.new_results_folder)
    folder_paths.append(path.new_temp_results_folder)
    folder_paths.append(path.new_userperfs_folder)
    folder_paths.append(path.new_userinnerperfs_folder)
    folder_paths.append(path.new_useraperfs_folder)

    folder_paths.append(path.ac_contest_results_folder)
    folder_paths.append(path.atcoder_unrated_performances_folder)
    folder_paths.append(path.results_folder)
    folder_paths.append(path.userperfs_folder)
    folder_paths.append(path.useraperfs_folder)
    folder_paths.append(path.userinnerperfs_folder)

    for folder_path in folder_paths:
        if not os.path.exists(folder_path): os.mkdir(folder_path)
    
    print("[ACUPD-Updater(create_folders)] finished!")

