import logging

import json
import os
import time
import requests
from bs4 import BeautifulSoup
from ..ACUPDlib import path
from ..ACUPDlib.type import FetchedContests, UserResult
from ..ACUPDlib.updatecheck import check_update_status
from typing import List

def main(name:str) -> str:
    if not check_update_status(): return ""
    if name not in ["ABC","ARC","AGC"]: return ""
    logging.info("[ACUPD-Updater(check-contest-results-update)]<" + name + "> start")

    check_status = "incomplete"
    if os.path.exists(path.fetch_tempdata):
        with open(path.fetch_tempdata, "r") as f:
            check_status = json.load(f)["status"]    

    if check_status == "completed": return ""
    elif check_status == "check failed":
        if name == "AGC":
            with open(path.fetch_tempdata, "w") as f:
                json.dump({"status": "incomplete"}, f, indent=4)
        return ""

    sleep_period = 0.5 #request間隔(秒)
    fetched_contests: FetchedContests #取得済みコンテスト
    with open(path.new_fetched_contests, "r") as f:
        fetched_contests = json.load(f)

    #複数回取得した同一コンテストの結果について, ユーザー名の齟齬(fetch中のユーザー名変更)がないかどうか調べる
    updatedflag = False
    pagenum = 1
    while not updatedflag:
        time.sleep(sleep_period)
        contests_archive_url = "https://atcoder.jp/contests/archive"
        contests_archive_params = {"category": 0, "page": pagenum, "ratedType": name, "lang": "ja"}
        contests_archive_html = requests.get(contests_archive_url, params=contests_archive_params)
        contests_archive_soup = BeautifulSoup(contests_archive_html.content, "html.parser")

        contests_list = contests_archive_soup.find_all("tr")

        #pagenumが終了後のコンテストのページ数を超えた場合, ループを抜ける
        if contests_list == []: break        

        for contest in reversed(contests_list):
            if len(contest.find_all("td")) < 4: continue
            if contest.find_all("td")[3].text == "-": continue 
            
            contest_name = contest.find_all("td")[1].find("a").get("href").split('/')[2]
            if contest_name not in fetched_contests["contests"]: continue
            
            contest_result1: List[UserResult]
            with open(path.new_results_folder + contest_name + ".json", "r") as f:
                contest_result1 = json.load(f)
            contest_result2: List[UserResult]
            with open(path.new_temp_results_folder + contest_name + ".json", "r") as f:
                contest_result2 = json.load(f)
            
            for idx, user_result1 in enumerate(contest_result1):
                user_result2 = contest_result2[idx]
                if user_result1["UserScreenName"] != user_result2["UserScreenName"]:
                    updatedflag = True
                    break
        pagenum += 1
     
    if updatedflag:
        with open(path.fetch_tempdata, "w") as f:
            json.dump({"status": "incomplete" if name == "AGC" else "check failed"}, f, indent=4)
    elif name == "AGC":
        with open(path.fetch_tempdata, "w") as f:
            json.dump({"status": "completed"}, f, indent=4)

    logging.info("[ACUPD-Updater(check-contest-results-update)]<" + name + "> end")  

    return ""
    