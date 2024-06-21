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
・過去のalgoコンテストすべてのresults(順位表データ)を取得する
・ユーザー名の変更がresults取得途中に行われた場合にも検出できるように取得は2回(2周)行い, ユーザー名の比較をする
'''

def fetch_results_files_full(ratedtype_str: str, ratedtype: int) -> None:

    request_period: float = 10 #request間隔(秒)
    fetched_contests: FetchedContests = {"contests":[]} #取得済みコンテスト
    contests_info: Dict[str, ContestInfo] = {} #コンテスト情報(日時・rated範囲)
    
    INF = pow(10,9)

    if os.path.exists(path.new_fetched_contests):
        with open(path.new_fetched_contests, "r") as f:
            fetched_contests = json.load(f)
            
    if os.path.exists(path.new_fetched_contests_info):
        with open(path.new_fetched_contests_info, "r") as f:
            contests_info = json.load(f)
            
    
    pagenum: int = 1
    while True:
        #終了後のコンテスト一覧を取得する
        print("[ACUPD-Updater(fetch_results_files_full)] <RatedType: " + ratedtype_str + ", Pages: " + str(pagenum) + "> now fetching...")
        time.sleep(request_period)
        contests_archive_url = "https://atcoder.jp/contests/archive"
        contests_archive_params = {"category": 0, "page": pagenum, "ratedType": ratedtype, "lang": "ja"}
        contests_archive_html = requests.get(contests_archive_url, params=contests_archive_params)
        contests_archive_soup = BeautifulSoup(contests_archive_html.content, "html.parser")
        print("[ACUPD-Updater(fetch_results_files_full)] <RatedType: " + ratedtype_str + ", Pages: " + str(pagenum) + "> fetched")
        

        contests_list = contests_archive_soup.find_all("tr")

        #pagenumが「終了後のコンテスト」のページ数を超えた場合, ループを抜ける
        if contests_list == []: break        

        for contest in reversed(contests_list):
            if len(contest.find_all("td")) < 4: continue 
            if contest.find_all("td")[3].text == "-": continue 
            
            contest_name = contest.find_all("td")[1].find("a").get("href").split('/')[2]

            fetched_contests["contests"].append(contest_name)

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

            #resultsをfetchしてくる
            contest_result_url = "https://atcoder.jp" + contest.find_all("td")[1].find("a").get("href") + "/results/json"
            print("[ACUPD-Updater(fetch_results_files_full)] <contest_name: " + contest_name + " > now fetching...")
            time.sleep(request_period)
            contest_result_html = requests.get(contest_result_url)
            contest_result_json = json.loads(contest_result_html.content)
            print("[ACUPD-Updater(fetch_results_files_full)] <contest_name: " + contest_name + " > fetched")

            #results(jsonファイル)を保存
            with open(path.new_results_folder + contest_name + ".json", "w") as f:
                json.dump(contest_result_json,f,indent=4)
            
            #取得済みコンテストの一覧(fetched_contests.json)を保存(プログラムの実行が中断されても大丈夫なようにコンテストごとに保存する)
            fetched_contests["contests"].sort(key=lambda x: (datetime.strptime(contests_info[x]["date"], "%Y-%m-%d %H:%M:%S"), x))
            with open(path.new_fetched_contests,"w") as f:
                json.dump(fetched_contests, f, indent=4)

            #コンテスト情報の一覧(fetched_contests_info.json)を保存
            with open(path.new_fetched_contests_info,"w") as f:
                json.dump(contests_info, f, indent=4)

        pagenum += 1
    

    print("[ACUPD-Updater(fetch_results_files_full)] finished!")


def fetch_results_files_light() -> None:

    request_period: float = 10 #request間隔(秒)
    fetched_contests: FetchedContests = {"contests":[]} #取得済みコンテスト
 
    with open(path.new_fetched_contests, "r") as f:
        fetched_contests = json.load(f)
    
    for contest_name in fetched_contests["contests"]:
        
        #resultsをfetchしてくる
        contest_result_url = "https://atcoder.jp/contests/" + contest_name + "/results/json"    
        print("[ACUPD-Updater(fetch_results_files_light)] <contest_name: " + contest_name + " > now fetching...")
        time.sleep(request_period)
        print("[ACUPD-Updater(fetch_results_files_light)] <contest_name: " + contest_name + " > fetched")
        contest_result_html = requests.get(contest_result_url)
        contest_result_json = json.loads(contest_result_html.content)

        #results(jsonファイル)を保存
        with open(path.new_temp_results_folder + contest_name + ".json", "w") as f:
            json.dump(contest_result_json,f,indent=4)

    print("[ACUPD-Updater(fetch_results_files_light)] finished!")


def detect_username_changes():
    
    username_changes: Dict[str,str] = {}

    fetched_contests: List[str]
    with open(path.new_fetched_contests, "r") as f:
        fetched_contests = json.load(f)["contests"]
    
    for contest_name in fetched_contests:
        old_results: List[UserResult]
        new_results: List[UserResult]

        with open(path.new_results_folder + contest_name + ".json", "r") as f:
            old_results = json.load(f)

        with open(path.new_temp_results_folder + contest_name + ".json") as f:
            new_results = json.load(f)

        for useridx in range(len(old_results)):
            old_username = old_results[useridx]["UserScreenName"]
            new_username = new_results[useridx]["UserScreenName"]

            if old_username != new_username:
                username_changes[old_username] = new_username
                print("[ACUPD-Updater(detect_username_changes)] detected! : " + old_username + " => " + new_username)


    for contest_name in fetched_contests:

        results:List[UserResult]
        with open(path.new_results_folder, "r") as f:
            results = json.load(f)

        for user_result in results:
            if user_result["UserScreenName"] in username_changes:
                user_result["UserScreenName"] = username_changes[user_result["UserScreenName"]]

        with open(path.new_results_folder + contest_name + ".json", "w") as f:
            json.dump(results, f, indent=4)
        
        print("[ACUPD-Updater(detect_username_changes)] <contest_name: " + contest_name + " > saved!")

    #変更に関連するユーザー名の一覧を保存(初回は使用しないため, 空のリストを出力)
    with open(path.renamed_users, "w") as f:
        json.dump([], f, indent=4)
    
    #ユーザー名の変化を保存(初回は使用しないため, 空のリストを出力)
    with open(path.username_changes, "w") as f:
        json.dump([], f, indent=4)

    shutil.rmtree(path.new_temp_results_folder)
    os.mkdir(path.new_temp_results_folder)            

    print("[ACUPD-Updater(detect_username_changes)] finished!")

def fetch_results():
    ratedtype = {"ABC":1, "ARC":2, "AGC":3}
    for ratedtype_str, ratedtype_num in ratedtype.items():
        fetch_results_files_full(ratedtype_str=ratedtype_str, ratedtype=ratedtype_num)

    fetch_results_files_light() #TODO: 更新が検出されなくなるまで繰り返しfetchするように修正
    detect_username_changes()
