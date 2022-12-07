import logging

import json
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..ACUPDlib import path
from ..ACUPDlib.type import FetchedContests, ContestInfo
from typing import List, Dict

def fetch_contest_results(ratedtype_str: str, ratedtype: int, savetype: str) -> None:

    sleep_period: float = 0.5 #request間隔(秒)
    fetched_contests: FetchedContests #取得済みコンテスト
    new_contests: List[str] = [] #今回新たに追加されるコンテスト
    contests_info: Dict[str, ContestInfo] #コンテスト情報(日時・rated範囲)
    INF = pow(10,9)

    if os.path.exists(path.new_fetched_contests):
        with open(path.new_fetched_contests, "r") as f:
            fetched_contests = json.load(f)
    else:
        with open(path.fetched_contests, "r") as f:
            fetched_contests = json.load(f)

    if os.path.exists(path.new_fetched_contests_info):
        with open(path.new_fetched_contests_info, "r") as f:
            contests_info = json.load(f)
    else:
        with open(path.fetched_contests_info, "r") as f:
            contests_info = json.load(f)

    if os.path.exists(path.new_contests):
        with open(path.new_contests, "r") as f:
            new_contests = json.load(f)
    

    #未取得のコンテストがあるかどうかを調べ, そのコンテスト結果を取得する
    pagenum: int = 1
    while True:
        #終了後のコンテスト一覧のhtmlを取得する
        logging.info("[ACUPD-Updater(fetch_contest_results)] <RatedType: " + ratedtype_str + ", Pages: " + str(pagenum) + "> now fetching...")
        time.sleep(sleep_period)
        contests_archive_url = "https://atcoder.jp/contests/archive"
        contests_archive_params = {"category": 0, "page": pagenum, "ratedType": ratedtype, "lang": "ja"}
        contests_archive_html = requests.get(contests_archive_url, params=contests_archive_params)
        contests_archive_soup = BeautifulSoup(contests_archive_html.content, "html.parser")

        contests_list = contests_archive_soup.find_all("tr")

        #pagenumが「終了後のコンテスト」のページ数を超えた場合, ループを抜ける
        if contests_list == []: break        

        for contest in reversed(contests_list):
            if len(contest.find_all("td")) < 4: continue
            if contest.find_all("td")[3].text == "-": continue 
            
            contest_name = contest.find_all("td")[1].find("a").get("href").split('/')[2]

            if contest_name not in fetched_contests["contests"]:
                #実装の関係上, 新たに追加するコンテストは1回の実行で1つまでにする
                if new_contests != []: continue 

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


            #resultsをfetchしてくる
            contest_result_url = "https://atcoder.jp" + contest.find_all("td")[1].find("a").get("href") + "/results/json"
            time.sleep(sleep_period)
            contest_result_html = requests.get(contest_result_url)
            contest_result_json = json.loads(contest_result_html.content)

            #results(jsonファイル)を保存
            if savetype == "newresults":
                with open(path.new_results_folder + contest_name + ".json", "w") as f:
                    json.dump(contest_result_json,f,indent=4)
            
            elif savetype == "newtempresults":
                with open(path.new_temp_results_folder + contest_name + ".json", "w") as f:
                    json.dump(contest_result_json,f,indent=4)

        pagenum += 1


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

    logging.info("[ACUPD-Updater(fetch_contest_results)] finished!")


def main(name:str) -> None:
    ratedtype = {"ABC":1, "ARC":2, "AGC":3}
    ratedtype_str = name.split("@")[0]
    savetype = name.split("@")[1]
        
    fetchflag = True
    if os.path.exists(path.fetch_tempdata):
        with open(path.fetch_tempdata, "r") as f:
            fetchflag = (json.load(f)["status"] == "incomplete")

    if fetchflag:
        fetch_contest_results(ratedtype_str, ratedtype[ratedtype_str], savetype)
