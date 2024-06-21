import create_folders
import fetch_contest_results
import calculate
import update_files
import copy_userdata

if __name__ == "__main__":
    create_folders.create_folders()
    fetch_contest_results.fetch_results()
    copy_userdata.prepare_userdata()
    calculate.calculate()
    update_files.update_files()
