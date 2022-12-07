import logging
import azure.durable_functions as df

import json
import os
import time
import requests
from bs4 import BeautifulSoup
from ..ACUPDlib import path
from ..ACUPDlib.type import FetchedContests

def update_check() -> bool:
    fetched_contests: FetchedContests
    with open(path.fetched_contests, "r") as f:
        fetched_contests = json.load(f)

    sleep_period = 0.5

    time.sleep(sleep_period)
    contests_archive_url = "https://atcoder.jp/contests/archive"
    contests_archive_params = {"ratedType": 0, "lang": "ja"}
    contests_archive_html = requests.get(contests_archive_url, params=contests_archive_params)
    contests_archive_soup = BeautifulSoup(contests_archive_html.content, "html.parser")

    contests_list = contests_archive_soup.find_all("tr")

    if contests_list == []: return False      

    for contest in contests_list:
        if len(contest.find_all("td")) < 4: continue
        if contest.find_all("td")[3].text == "-": continue 
        if contest.find_all("td")[1].find_all("span")[0].text != "Ⓐ": continue

        contest_name = contest.find_all("td")[1].find("a").get("href").split('/')[2]

        return (contest_name not in fetched_contests["contests"])

    logging.info("[ACUPD-Updater] updatecheck finished")

    return False


def orchestrator_function(context: df.DurableOrchestrationContext):
    logging.info("[ACUPD-Updater] orchestrator start")

    if os.path.exists(path.new_contests) or update_check():
        CALC_RANGE = 1000 #ACUPD-calculate 1回の呼び出しにつき何人分処理するか
        UPDATE_REPO_RANGE = 400 #ACUPD-update-repository 1回の呼び出しにつき何人分処理するか
        UPDATE_FILE_RANGE = 1000 #ACUPD-misc-functions(update_contestants) 1回の呼び出しにつき何人分処理するか
        MAX_CONTESTANTS_COUNT = 15000 #コンテスト参加者の最大人数
        
        #一時ファイル用のフォルダを作成
        yield context.call_activity("ACUPD-misc-functions", "create_tempfolders")

        #一時ファイルの削除
        yield context.call_activity("ACUPD-misc-functions", "delete_tempfiles")

        #コンテスト結果を取得
        for ratedtype in ["ABC","ARC","AGC"]:
            yield context.call_activity("ACUPD-fetch-contest-results",ratedtype + "@newresults")

        for _ in range(10):
            for ratedtype in ["ABC","ARC","AGC"]:
                yield context.call_activity("ACUPD-fetch-contest-results",ratedtype + "@newtempresults")
        
            for ratedtype in ["ABC","ARC","AGC"]:
                yield context.call_activity("ACUPD-check-contest-results-update",ratedtype)
                
            yield context.call_activity("ACUPD-misc-functions", "move_temp_results")
                
        #ユーザー名変更の検出・修正
        yield context.call_activity("ACUPD-correct-usernames","")

        #内部レート・内部パフォーマンス・パフォーマンスの計算に関連するファイルをコピー
        for startidx in range(0, MAX_CONTESTANTS_COUNT+UPDATE_FILE_RANGE, UPDATE_FILE_RANGE):        
            endidx = startidx + UPDATE_REPO_RANGE
            yield context.call_activity("ACUPD-misc-functions", "copy_userdata@" + str(startidx) + "-" + str(endidx))

        #内部レート・内部パフォーマンス・パフォーマンスの計算
        yield context.call_activity("ACUPD-calculate","init") #計算準備
        for default_aperf in ["default", "800", "1000", "1200", "1600", "2000"]:
            
            #内部レートの計算
            for startidx in range(0,MAX_CONTESTANTS_COUNT+CALC_RANGE, CALC_RANGE):
                endidx = startidx + CALC_RANGE
                yield context.call_activity("ACUPD-calculate","aperf@"+ str(startidx) + "-" + str(endidx) +"@" + default_aperf) 

            #内部パフォーマンス・パフォーマンスの計算
            for startidx in range(0,MAX_CONTESTANTS_COUNT+CALC_RANGE, CALC_RANGE):
                endidx = startidx + CALC_RANGE
                yield context.call_activity("ACUPD-calculate","perf@"+ str(startidx) + "-" + str(endidx)) 

            #パフォーマンスの値に齟齬がないかどうかチェック
            yield context.call_activity("ACUPD-calculate","check")

            #内部パフォーマンス・パフォーマンスの保存
            for startidx in range(0,MAX_CONTESTANTS_COUNT+CALC_RANGE, CALC_RANGE):
                endidx = startidx + CALC_RANGE
                yield context.call_activity("ACUPD-calculate","save@"+ str(startidx) + "-" + str(endidx) +"@" + default_aperf) 
        
        #更新したファイルをGitHubに上げる 
        yield context.call_activity("ACUPD-update-repository", "renamed_users")
        yield context.call_activity("ACUPD-update-repository", "new_contest_info")
        for startidx in range(0, MAX_CONTESTANTS_COUNT, UPDATE_REPO_RANGE):        
            endidx = startidx + UPDATE_REPO_RANGE
            yield context.call_activity("ACUPD-update-repository", "contestants@" + str(startidx) + "-" + str(endidx))

        #内部レート・内部パフォーマンス・パフォーマンスのファイルを更新
        yield context.call_activity("ACUPD-misc-functions", "update_renamed_users")        

        for startidx in range(0,MAX_CONTESTANTS_COUNT, UPDATE_FILE_RANGE):
            endidx = startidx + UPDATE_FILE_RANGE
            yield context.call_activity("ACUPD-misc-functions", "update_contestants@" + str(startidx) + "-" + str(endidx))            

        #コンテスト結果(results)のファイルを更新
        yield context.call_activity("ACUPD-misc-functions", "update_results")

        #取得済みコンテスト一覧を更新
        yield context.call_activity("ACUPD-misc-functions", "update_fetched_contests")

        #デフォルト内部レート一覧を更新
        yield context.call_activity("ACUPD-misc-functions", "update_defaultaperfs")

        #一時ファイルの削除
        yield context.call_activity("ACUPD-misc-functions", "delete_tempfiles")


main = df.Orchestrator.create(orchestrator_function)

