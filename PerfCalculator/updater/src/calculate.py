import json
import os
import math
import shutil
from datetime import datetime
from collections import deque
from decimal import Decimal, ROUND_HALF_UP
from lib import path
from lib.type import ContestInfo, UserResult, CalcTempData, InnerPerfInfo
from typing import List, Dict, Deque


INF = math.pow(10,9)

#デフォルト内部レート一覧をac_contest_resultsからtempdataにコピーする
def fetch_defaultaperfs() -> None:
    if os.path.exists(path.defaultaperfs):
        shutil.copyfile(path.defaultaperfs, path.new_defaultaperfs)
    
    print("[ACUPD-Updater(fetch_defaultaperfs)] finished")


#コンテストの情報からデフォルト内部レートを計算
def calc_default_aperf(contest_name: str, fetched_contests_info: Dict[str, ContestInfo]) -> int:
    contest_dt = datetime.strptime(fetched_contests_info[contest_name]["date"], "%Y-%m-%d %H:%M:%S")

    if fetched_contests_info[contest_name]["upper_rating_limit"] == INF: #AGC級
        agc034_dt = datetime.strptime(fetched_contests_info["agc034"]["date"], "%Y-%m-%d %H:%M:%S")

        if contest_dt < agc034_dt: return 1600
        else: return 1200

    elif fetched_contests_info[contest_name]["upper_rating_limit"] == 2799: #ARC級
        arc104_dt = datetime.strptime(fetched_contests_info["arc104"]["date"], "%Y-%m-%d %H:%M:%S")

        if contest_dt < arc104_dt: return 1600
        else: return 1000

    return 800 #ABC級


#初期設定
def calc_init() -> None:
    print("[ACUPD-Updater(calculate-calc_init)] now initializing...")
        
    #今回追加されたコンテストの一覧を取得
    contest_name: str
    with open(path.new_contests, "r") as f:
        contest_name = json.load(f)[0]

    #取得済みコンテストの一覧(fetched_contests.json)を取得
    fetched_contests_info: Dict[str, ContestInfo]
    with open(path.new_fetched_contests_info, "r") as f:
        fetched_contests_info = json.load(f)

    #コンテスト結果(results)を取得
    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    is_ratedcontest: bool = False
    for user_result in contest_result:
        is_ratedcontest |= user_result["IsRated"]
        if is_ratedcontest: break

    outputdict: CalcTempData = {"contest_name": contest_name, "is_ratedcontest": is_ratedcontest, \
        "pred_default_aperf": calc_default_aperf(contest_name,fetched_contests_info), \
        "user_latest_aperf": {}, "aperflist":[], \
        "user_innerperf": {}, "user_perf": {}, "finished": False, "is_matched": False}
    
    with open(path.calculate_tempdata, "w") as f:
        json.dump(outputdict, f, indent=4)


#ある参加者のあるコンテスト開始時点での内部レートを計算する
def calc_useraperf(username: str, contest_name: str, fetched_contests_info: Dict[str, ContestInfo], default_aperf: int) -> float:

    aperf_num: Decimal = Decimal(0.0)
    aperf_den: Decimal = Decimal(0.0)

    if os.path.exists(path.new_userinnerperfs_folder + username + ".json"):
    
        user_innerperf: Dict[str, InnerPerfInfo]
        with open(path.new_userinnerperfs_folder + username + ".json","r") as f:
            user_innerperf = json.load(f)

        #コンテストの実施日の昇順にソート
        listed_user_innerperf = sorted(user_innerperf.items(), key=lambda x: (datetime.strptime(fetched_contests_info[x[0]]["date"], "%Y-%m-%d %H:%M:%S"), x[0]))
        user_innerperf = dict((x,y) for x,y in listed_user_innerperf)

        contest_dt :datetime = datetime.strptime(fetched_contests_info[contest_name]["date"], "%Y-%m-%d %H:%M:%S")

        #内部レートの計算
        power: Decimal = Decimal(1)
        for contest, innerperf_info in user_innerperf.items():
            if not innerperf_info["IsRated"]: continue
            if (contest_dt, contest_name) <= (datetime.strptime(fetched_contests_info[contest]["date"], "%Y-%m-%d %H:%M:%S"), contest): continue

            innerperf = Decimal(str(innerperf_info["InnerPerf"]))

            power *= Decimal("0.9")
            aperf_num = (aperf_num + innerperf) * Decimal("0.9")
            aperf_den += power

    if aperf_den == 0.0: return default_aperf
    return float(aperf_num/aperf_den)


#あるコンテストにおける参加者全員の内部レート・内部パフォーマンス・パフォーマンスを計算して保存する
def calc_useraperf_all(default_aperf: int) -> None:

    tempdata: CalcTempData
    with open(path.calculate_tempdata, "r") as f:
        tempdata = json.load(f)
    
    contest_name = tempdata["contest_name"]
    is_ratedcontest = tempdata["is_ratedcontest"]
    aperflist = tempdata["aperflist"] #rated参加者全員分(unratedコンの場合はrated範囲内の参加者全員)の内部レートのリスト
    user_latest_aperf = tempdata["user_latest_aperf"] #全参加者の内部レートを記録した辞書

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    fetched_contests_info: Dict[str, ContestInfo]
    with open(path.new_fetched_contests_info, "r") as f:
        fetched_contests_info = json.load(f)

    print("[ACUPD-Updater(calculate-calc_useraperf_all)] <contest: " + contest_name + ", default_aperf: " + str(default_aperf) + "> now calculating...")

    for user_result in contest_result:
        username = user_result["UserScreenName"]
        
        user_latest_aperf[username] = calc_useraperf(username, contest_name, fetched_contests_info, default_aperf)

        if user_result["IsRated"]: aperflist.append(user_latest_aperf[username])
        elif is_ratedcontest: pass
        elif user_result["OldRating"] > fetched_contests_info[contest_name]["upper_rating_limit"]: pass
        elif user_result["OldRating"] < fetched_contests_info[contest_name]["lower_rating_limit"]: pass
        else: aperflist.append(user_latest_aperf[username])
    
        #内部レートの保存
        aperf_tempdict: Dict[str, float] = {}
        if os.path.exists(path.new_useraperfs_folder + username + ".json"):
            with open(path.new_useraperfs_folder + username + ".json", "r") as f:
                aperf_tempdict = json.load(f)

        aperf_tempdict[contest_name] = user_latest_aperf[username]
        with open(path.new_useraperfs_folder + username + ".json", "w") as f:
            json.dump(aperf_tempdict,f,indent=4)

    tempdata["aperflist"] = aperflist
    tempdata["user_latest_aperf"] = user_latest_aperf

    with open(path.calculate_tempdata, "w") as f:
        json.dump(tempdata, f, indent=4)
    
    print("[ACUPD-Updater(calculate-calc_useraperf_all)] <contest: " + contest_name + ", default_aperf: " + str(default_aperf)+ "> calculation finished")



#順位と全参加者の内部レートが与えられたとき, 各参加者の内部パフォーマンスを計算する
def calc_userperf(place: float, aperflist: List[float], is_unrated: bool, unrated_aperf: float = -1) -> float:
    ok: float = -10000.0
    ng: float = 10000.0
    
    for _ in range(25):
        mid: float = (ok+ng)/2.0

        fmid: float = 0.0
        for aperf in aperflist:
            fmid += 1.0/(1.0 + math.pow(6.0, (mid - aperf)/400.0))
        
        if is_unrated:
            fmid += 1.0/(1.0 + math.pow(6.0, (mid - unrated_aperf)/400.0))
        
        if fmid >= place-0.5: ok = mid
        else: ng = mid

    return ok


#ある順位のパフォーマンスを計算する
def calc_userperf_by_place(ratedplace: int, ratedcnt: int, contest_name: str, aperflist: List[float], contest_result: List[UserResult], deq: Deque[int], is_ratedcontest:bool, user_innerperf: Dict[str, float], user_latest_aperf: Dict[str, float], fetched_contests_info: Dict[str, ContestInfo], last_place:int, last_perf:int) -> None:
    place: float = ratedplace + max(0.0, (ratedcnt-1)/2.0) #fractional rankingでの順位を算出
    unratedplace: float = ratedplace + ratedcnt/2.0 #unratedの場合(該当順位の人数を1増やした場合)のfractional rankingでの順位を算出
    
    rated_perf = calc_userperf(place, aperflist, False)
    while deq:
        idx = deq.popleft()

        username = contest_result[idx]["UserScreenName"]

        if is_ratedcontest:
            if contest_result[idx]["Place"] == last_place: 
                user_innerperf[username] = last_perf

            elif not contest_result[idx]["IsRated"]: 
                user_innerperf[username] = calc_userperf(unratedplace, aperflist, True, user_latest_aperf[username])
            else: 
                user_innerperf[username] = rated_perf

        else:
            if contest_result[idx]["OldRating"] > fetched_contests_info[contest_name]["upper_rating_limit"]:
                user_innerperf[username] = calc_userperf(unratedplace, aperflist, True, user_latest_aperf[username])
            elif contest_result[idx]["OldRating"] < fetched_contests_info[contest_name]["lower_rating_limit"]:
                user_innerperf[username] = calc_userperf(unratedplace, aperflist, True, user_latest_aperf[username])
            else:
                user_innerperf[username] = rated_perf


#あるコンテストにおける全参加者の内部パフォーマンス(400未満の補正なし), パフォーマンス(補正あり)を計算
def calc_userperf_all() -> None:
    print("[ACUPD-Updater(calculate-calc_userperf_all)] now calculating...")

    tempdata: CalcTempData
    with open(path.calculate_tempdata, "r") as f:
        tempdata = json.load(f)
    
    contest_name = tempdata["contest_name"]
    is_ratedcontest = tempdata["is_ratedcontest"]
    aperflist = tempdata["aperflist"]
    user_latest_aperf = tempdata["user_latest_aperf"]
    user_innerperf = tempdata["user_innerperf"]
    user_perf = tempdata["user_perf"]

    contest_result: List[UserResult]
    with open(path.new_results_folder + contest_name + ".json", "r") as f:
        contest_result = json.load(f)

    fetched_contests_info: Dict[str, ContestInfo]
    with open(path.new_fetched_contests_info, "r") as f:
        fetched_contests_info = json.load(f)

    #0完のパフォーマンスだけが何故か計算式と合わないので, 該当パフォーマンスだけcontest_resultから引っ張ってきてlast_perfに格納しておく(有識者いませんか)
    last_place: int = 0
    last_perf: int = 0
    for user_result in contest_result:
        last_place = max(last_place, user_result["Place"])

        if last_place == user_result["Place"] and user_result["IsRated"]:
            last_perf = user_result["Performance"]

    #順位ごとにパフォーマンスを計算(同順位はまとめて計算)
    deq: Deque[int] = deque()
    ratedplace = 1
    ratedcnt: int = 0
    for useridx in range(len(contest_result)):

        if not deq:
            deq.append(useridx)

        elif contest_result[useridx]["Place"] == contest_result[deq[0]]["Place"]:
            deq.append(useridx)

        else:
            calc_userperf_by_place(ratedplace, ratedcnt, contest_name, aperflist, contest_result, deq, \
                is_ratedcontest, user_innerperf, user_latest_aperf, fetched_contests_info, last_place, last_perf)

            deq.append(useridx)
            ratedplace += ratedcnt
            ratedcnt = 0

        if contest_result[useridx]["IsRated"]: ratedcnt += 1
        elif is_ratedcontest: pass
        elif contest_result[useridx]["OldRating"] > fetched_contests_info[contest_name]["upper_rating_limit"]: pass
        elif contest_result[useridx]["OldRating"] < fetched_contests_info[contest_name]["lower_rating_limit"]: pass
        else: ratedcnt += 1
    
    calc_userperf_by_place(ratedplace, ratedcnt, contest_name, aperflist, contest_result, deq, \
        is_ratedcontest, user_innerperf, user_latest_aperf, fetched_contests_info, last_place, last_perf)

    ratedplace += ratedcnt
    
    #agc001だけはパフォーマンスを1600を中心に1.5倍に引き伸ばす
    if contest_name == "agc001":
        for username, innerperf in user_innerperf.items():
            if innerperf != last_perf:
                user_innerperf[username] = (innerperf-1600)*1.5 + 1600

    #パフォーマンス400未満の補正 & 四捨五入して整数化
    for username, innerperf in user_innerperf.items():
        user_perf[username] = min(innerperf, fetched_contests_info[contest_name]["upper_rating_limit"] + 401)
        if user_perf[username] < 400: user_perf[username] = 400.0/math.exp((400.0-user_perf[username])/400.0)
        user_perf[username] = int(Decimal(user_perf[username]).quantize(Decimal('0'), rounding=ROUND_HALF_UP))
        user_innerperf[username] = int(Decimal(user_innerperf[username]).quantize(Decimal('0'), rounding=ROUND_HALF_UP))

    #user_innerperfとuser_perfを一時保存
    tempdata["user_innerperf"] = user_innerperf
    tempdata["user_perf"] = user_perf
    with open(path.calculate_tempdata, "w") as f:
        json.dump(tempdata, f, indent=4)
    
    print("[ACUPD-Updater(calculate-calc_userperf_all)] calculation finished")


#計算したパフォーマンスと, 実際のパフォーマンスの値に齟齬がないかを調べる
def is_matched() -> None:
    print("[ACUPD-Updater(calculate-is_matched)] now checking...")

    tempdata: CalcTempData
    with open(path.calculate_tempdata, "r") as f:
        tempdata = json.load(f)

    user_perf = tempdata["user_perf"]

    contest_result: List[UserResult]
    with open(path.new_results_folder + tempdata["contest_name"] + ".json", "r") as f:
        contest_result = json.load(f)

    mismatched_dict: Dict[str, Dict[str,float]] = {}
    for user_result in contest_result:
        if not user_result["IsRated"]: continue 
        username = user_result["UserScreenName"]
        perf = user_result["Performance"]
        if perf < 400: perf = 400.0/math.exp((400.0-perf)/400.0)
        perf = int(Decimal(perf).quantize(Decimal('0'), rounding=ROUND_HALF_UP))

        if abs(user_perf[username] - perf) > 1:
            mismatched_dict[username] = {"Place": user_result["Place"], "Calculated":user_perf[username], "Actual":perf}
    
    if mismatched_dict != {} : print(mismatched_dict)
    
    tempdata["is_matched"] = (mismatched_dict == {})
    with open(path.calculate_tempdata, "w") as f:
        json.dump(tempdata, f, indent=4)


def save_userperfs(default_aperf: int) -> None:
    
    tempdata: CalcTempData
    with open(path.calculate_tempdata, "r") as f:
        tempdata = json.load(f)

    contest_name = tempdata["contest_name"]
    user_innerperf = tempdata["user_innerperf"]
    user_perf = tempdata["user_perf"]

    contest_result: List[UserResult]
    with open(path.new_results_folder + tempdata["contest_name"] + ".json", "r") as f:
        contest_result = json.load(f)

    print("[ACUPD-Updater(calculate-save_userperfs)] <default_aperf: " + str(default_aperf)+ "> now saving...")

    for user_result in contest_result:
        username = user_result["UserScreenName"]

        #内部パフォーマンスの保存
        innerperf_tempdict: Dict[str, InnerPerfInfo] = {}   
        if os.path.exists(path.new_userinnerperfs_folder + username + ".json"):
            with open(path.new_userinnerperfs_folder + username + ".json", "r") as f:
                innerperf_tempdict = json.load(f)

        innerperf_tempdict[contest_name] = {"InnerPerf": user_innerperf[username], "IsRated": user_result["IsRated"]}
        
        with open(path.new_userinnerperfs_folder + username + ".json", "w") as f:
            json.dump(innerperf_tempdict,f,indent=4)

        #パフォーマンスの保存
        if not user_result["IsRated"]: 
            perf_tempdict: Dict[str, float] = {}
            if os.path.exists(path.new_userperfs_folder + username + ".json"):
                with open(path.new_userperfs_folder + username + ".json", "r") as f:
                    perf_tempdict = json.load(f)

            perf_tempdict[contest_name] = user_perf[username]
            
            with open(path.new_userperfs_folder + username + ".json", "w") as f:
                json.dump(perf_tempdict,f,indent=4)

    #デフォルト内部レートを記録
    aperf_tempdict: Dict[str, float] = {}
    if os.path.exists(path.new_defaultaperfs):
        with open(path.new_defaultaperfs, "r") as f:
            aperf_tempdict = json.load(f)

    aperf_tempdict[contest_name] = default_aperf
    
    with open(path.new_defaultaperfs,"w") as f:
        json.dump(aperf_tempdict, f, indent=4)

    print("[ACUPD-Updater(calculate-save_userperfs)] <default_aperf: " + str(default_aperf)+ "> saving finished")



def calculate():
    fetch_defaultaperfs()

    finished: bool = False
    #for default_aperf_str in ["default", "800", "1000", "1200", "1600", "2000"]:
    for default_aperf_str in ["default"]:
        calc_init()

        tempdata:CalcTempData
        with open(path.calculate_tempdata, "r") as f:
            tempdata = json.load(f)

        default_aperf:int = tempdata["pred_default_aperf"] if default_aperf_str == "default" else int(default_aperf_str)

        #内部レートの計算
        calc_useraperf_all(default_aperf)

        #内部パフォーマンス・パフォーマンスの計算
        calc_userperf_all()

        #パフォーマンスの値に齟齬がないかどうかチェック
        is_matched()

        #内部パフォーマンス・パフォーマンスの保存
        with open(path.calculate_tempdata, "r") as f:
            tempdata = json.load(f)
            
            if tempdata["is_matched"]: 
                save_userperfs(default_aperf)
                finished = True
                break
    
    assert finished, "resultsファイルのperfに一致するaperfが見つかりませんでした"