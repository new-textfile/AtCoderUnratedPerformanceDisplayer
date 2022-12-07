import os

#ac_contest_resultsフォルダ
fetched_contests = os.environ["PATH_TO_AC_CONTEST_RESULTS"] + "fetched_contests.json"
fetched_contests_info =  os.environ["PATH_TO_AC_CONTEST_RESULTS"] + "fetched_contests_info.json"
defaultaperfs =  os.environ["PATH_TO_AC_CONTEST_RESULTS"] + "default_aperfs.json"
results_folder =  os.environ["PATH_TO_AC_CONTEST_RESULTS"] + "results/"
useraperfs_folder = os.environ["PATH_TO_AC_CONTEST_RESULTS"] + "useraperfs/"
userinnerperfs_folder =  os.environ["PATH_TO_AC_CONTEST_RESULTS"] + "userinnerperfs/"

#AtCoderUnratedPerformancesフォルダ
userperfs_folder = os.environ["PATH_TO_ATCODER_UNRATED_PERFORMANCES"] + "userperfs/"

#tempdataフォルダ
tempdata_folder = os.environ["PATH_TO_TEMPDATA"]
new_fetched_contests = os.environ["PATH_TO_TEMPDATA"] + "fetched_contests.json"
new_fetched_contests_info = os.environ["PATH_TO_TEMPDATA"] + "fetched_contests_info.json"
new_defaultaperfs = os.environ["PATH_TO_TEMPDATA"] + "default_aperfs.json"
new_results_folder =  os.environ["PATH_TO_TEMPDATA"] + "results/"
new_temp_results_folder =  os.environ["PATH_TO_TEMPDATA"] + "tempresults/"
new_userinnerperfs_folder = os.environ["PATH_TO_TEMPDATA"] + "userinnerperfs/"
new_useraperfs_folder =  os.environ["PATH_TO_TEMPDATA"] + "useraperfs/"
new_userperfs_folder = os.environ["PATH_TO_TEMPDATA"] + "userperfs/"
new_contests = os.environ["PATH_TO_TEMPDATA"] + "new_contests.json"
calculate_tempdata = os.environ["PATH_TO_TEMPDATA"] + "calclulate_tempdata.json"
fetch_tempdata = os.environ["PATH_TO_TEMPDATA"] + "fetch_tempdata.json"
renamed_users = os.environ["PATH_TO_TEMPDATA"] + "renamed_users.json"
username_changes = os.environ["PATH_TO_TEMPDATA"] + "username_changes.json"