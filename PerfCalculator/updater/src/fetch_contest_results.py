import json
import os
import time
import requests
import shutil
from bs4 import BeautifulSoup
from datetime import datetime
from lib import path
from lib.type import FetchedContests, ContestInfo, UserResult
from typing import List, Dict, Set


'''
・未取得のコンテストのうち、最も古いコンテストのresultsを取得する
・fetched_contestsに記録されている各コンテストについて, resultsを取得する
'''

def fetch_html(url, params_dict={}):
    for i in range(9):
        try:
            res_html = requests.get(url,params=params_dict)
            return res_html
        except:
            print("fetch failed...")
            time.sleep(30)

    res_html = requests.get(url,params=params_dict)
    return res_html    

def check_update_status() -> None:

    request_period: float = 10 #request間隔(秒)
    fetched_contests: FetchedContests #取得済みコンテスト
    new_contests: List[str] = [] #今回新たに追加されるコンテスト
    contests_info: Dict[str, ContestInfo] #コンテスト情報(日時・rated範囲)
    INF = pow(10,9)

    with open(path.fetched_contests, "r") as f:
        fetched_contests = json.load(f)

    with open(path.fetched_contests_info, "r") as f:
        contests_info = json.load(f)

    
    print("[ACUPD-Updater(check_update_status)] now fetching contest history...")
    time.sleep(request_period)
    contests_archive_url = "https://atcoder.jp/contests/archive"
    contests_archive_params = {"ratedType": 0, "lang": "ja"}
    contests_archive_html = fetch_html(contests_archive_url, contests_archive_params)
    contests_archive_soup = BeautifulSoup(contests_archive_html.content, "html.parser")
    print("[ACUPD-Updater(check_update_status)] fetched")

    contests_list = contests_archive_soup.find_all("tr")

    status = False
    if contests_list != []:
        for contest in reversed(contests_list):
            if len(contest.find_all("td")) < 4: continue
            if contest.find_all("td")[3].text == "-": continue 
            if contest.find_all("td")[1].find_all("span")[0].text != "Ⓐ": continue
            
            contest_name = contest.find_all("td")[1].find("a").get("href").split('/')[2]
            if contest_name == "wtf22-day1" or contest_name == "wtf22-day2": continue #wtf22はRated対象の欄に"2000~"が記入されているがUnratedなので弾く

            if contest_name not in fetched_contests["contests"]:

                print("[ACUPD-Updater(check_update_status)] <contest_name: " + contest_name + "> now fetching...")
                time.sleep(request_period)
                contest_result_url = "https://atcoder.jp/contests/" + contest_name + "/results/json"
                contest_result_list = json.loads(fetch_html(contest_result_url).content)
                status = (len(contest_result_list) > 0)
                print("[ACUPD-Updater(check_update_status)] <contest_name: " + contest_name + "> fetched")
                
                if status:
                    fetched_contests["contests"].append(contest_name)
                    new_contests.append(contest_name)

                    #resultsからコンテスト情報(日時・rated範囲)を抽出したものをcontests_infoに記録
                    contests_info[contest_name] = {"date": contest.find("time").text[:19], "upper_rating_limit": -1, "lower_rating_limit": -1}
                    
                    if contest.find_all("td")[3].text == "All":
                        contests_info[contest_name]["upper_rating_limit"] = INF
                        contests_info[contest_name]["lower_rating_limit"] = 0
                    else:
                        if contest.find_all("td")[3].text.replace(" ","").split("~")[1] == "":
                            contests_info[contest_name]["upper_rating_limit"] = INF
                        else:
                            contests_info[contest_name]["upper_rating_limit"] = int(contest.find_all("td")[3].text.replace(" ","").split("~")[1])
                            
                        if contest.find_all("td")[3].text.replace(" ","").split("~")[0] == "":
                            contests_info[contest_name]["lower_rating_limit"] = 0
                        else:
                            contests_info[contest_name]["lower_rating_limit"] = int(contest.find_all("td")[3].text.replace(" ","").split("~")[0])

                break

    if not os.path.exists(path.tempdata_folder): os.mkdir(path.tempdata_folder)

    with open(path.update_status, "w") as f:
        json.dump({"status": status}, f, indent=4)
    
    if new_contests == []:
        return
    

    #取得済みコンテストの一覧(fetched_contests.json)を作成
    fetched_contests["contests"].sort(key=lambda x: (datetime.strptime(contests_info[x]["date"], "%Y-%m-%d %H:%M:%S"), x))
    with open(path.new_fetched_contests,"w") as f:
        json.dump(fetched_contests, f, indent=4)

    #コンテスト情報の一覧(fetched_contests_info.json)を更新
    with open(path.new_fetched_contests_info,"w") as f:
        json.dump(contests_info, f, indent=4)
    
    #今回追加されたコンテストの一覧(added_contest.json)を作成
    with open(path.new_contests, "w") as f:
        json.dump(new_contests, f, indent=4)
    
    with open(path.tempdata_folder + "added_contest_name", "w") as f:
        f.write(new_contests[0])

    print("[ACUPD-Updater(check_update_status)] finished")


def fetch_results_files() -> None:

    request_period: float = 10 #request間隔(秒)
    fetched_contests: FetchedContests = {"contests":[]} #取得済みコンテスト
    new_contest: str

    
    with open(path.new_fetched_contests, "r") as f:
        fetched_contests = json.load(f)

    #新規追加のコンテストをfetchする(名前変更検出のため, 新規追加分 -> 過去すべてのresults -> 新規追加分(2回目) の順番で取得する)
    with open(path.new_contests) as f:
        new_contest = json.load(f)[0]
        
    if not os.path.exists(path.new_results_folder + new_contest + ".json"):
        #resultsをfetchしてくる
        contest_result_url = "https://atcoder.jp/contests/" + new_contest + "/results/json"    
        print("[ACUPD-Updater(fetch_results_files)] <contest_name: " + new_contest + " > now fetching...")
        time.sleep(request_period)
        print("[ACUPD-Updater(fetch_results_files)] <contest_name: " + new_contest + " > fetched")
        contest_result_html = fetch_html(contest_result_url)
        contest_result_json = json.loads(contest_result_html.content)

        #results(jsonファイル)を保存
        with open(path.new_results_folder + new_contest + ".json", "w") as f:
            json.dump(contest_result_json,f,indent=4)


    assert fetched_contests["contests"][-1] == new_contest, "new_contestがリストの末尾にありません"
    
    for contest_name in fetched_contests["contests"]:
        if os.path.exists(path.new_temp_results_folder + contest_name + ".json"): continue
        
        #resultsをfetchしてくる
        contest_result_url = "https://atcoder.jp/contests/" + contest_name + "/results/json"    
        print("[ACUPD-Updater(fetch_results_files)] <contest_name: " + contest_name + " > now fetching...")
        time.sleep(request_period)
        print("[ACUPD-Updater(fetch_results_files)] <contest_name: " + contest_name + " > fetched")
        contest_result_html = fetch_html(contest_result_url)
        contest_result_json = json.loads(contest_result_html.content)

        #results(jsonファイル)を保存
        with open(path.new_temp_results_folder + contest_name + ".json", "w") as f:
            json.dump(contest_result_json,f,indent=4)

    print("[ACUPD-Updater(fetch_results_files)] finished!")



def detect_username_changes() -> None:
    
    username_changes: Dict[str,str] = {}
    renamed_users: Set[str] = set() #名前の変更を行ったユーザーの変更前・変更後の名前を保持するset
    new_contest: str

    fetched_contests: List[str]
    with open(path.new_fetched_contests, "r") as f:
        fetched_contests = json.load(f)["contests"]

    with open(path.new_contests, "r") as f:
        new_contest = json.load(f)[0]

    for contest_name in fetched_contests:
        

        old_results: List[UserResult]
        new_results: List[UserResult]

        if contest_name == new_contest:
            with open(path.new_results_folder + contest_name + ".json", "r") as f:
                old_results = json.load(f)
        else:
            with open(path.results_folder + contest_name + ".json", "r") as f:
                old_results = json.load(f)


        with open(path.new_temp_results_folder + contest_name + ".json") as f:
            new_results = json.load(f)

        for useridx in range(len(old_results)):
            old_username = old_results[useridx]["UserScreenName"]
            new_username = new_results[useridx]["UserScreenName"]

            if old_username != new_username:
                username_changes[old_username] = new_username
                renamed_users.add(old_username)
                renamed_users.add(new_username)
                print("[ACUPD-Updater(detect_username_changes)] detected! : " + old_username + " => " + new_username)


    for contest_name in fetched_contests:

        if contest_name == new_contest:
            shutil.copy(path.new_temp_results_folder + contest_name + ".json", path.new_results_folder + contest_name + ".json")

        else:
            results:List[UserResult]
            with open(path.results_folder + contest_name + ".json", "r") as f:
                results = json.load(f)

            for user_result in results:
                if user_result["UserScreenName"] in username_changes:
                    user_result["UserScreenName"] = username_changes[user_result["UserScreenName"]]

            with open(path.new_results_folder + contest_name + ".json", "w") as f:
                json.dump(results, f, indent=4)
        
        print("[ACUPD-Updater(detect_username_changes)] <contest_name: " + contest_name + " > saved!")

    #変更に関連するユーザー名の一覧を保存
    with open(path.renamed_users, "w") as f:
        json.dump(list(renamed_users), f, indent=4)
    
    #ユーザー名の変化を保存
    with open(path.username_changes, "w") as f:
        json.dump(username_changes, f, indent=4)

    shutil.rmtree(path.new_temp_results_folder)
    os.mkdir(path.new_temp_results_folder)


    print("[ACUPD-Updater(detect_username_changes)] finished!")



def fetch_results():
    check_update_status()

    with open(path.update_status, "r") as f:
        update_status = json.load(f)["status"]
        assert update_status, "更新要素が存在しないか, resultsが用意されていないコンテストが存在します"

    fetch_results_files()
    detect_username_changes()
