// ==UserScript==
// @name         AtCoderUnratedPerfDisplayer
// @namespace    https://new-textfile.github.io/
// @version      1.0
// @description  Unrated参加したRated Algoコンテストのパフォーマンス推定値を表示します。
// @author       new_textfile
// @match        https://atcoder.jp/users/*/history*
// @exclude      https://atcoder.jp/users/*/history?*contestType=heuristic*
// @grant        none
// ==/UserScript==

(async function() {
    'use strict';

    if(location.href.match(/https:\/\/atcoder.jp\/users\/.*\/history\/share\/.*/g) === null){
            await displayperf_competition_history(); //コンテスト成績表ページについての処理を行う
    }
    else{
        await displayperf_contest_result(); //コンテスト成績証ページについての処理を行う
    }

})();

async function displayperf(userperfs){
    let rows_cnt = document.querySelectorAll("tr").length;

    for(let rownum = rows_cnt-1; rownum >= 1; rownum--){
        let contest = document.querySelectorAll("tr")[rownum].querySelectorAll("td");
        let contest_name = contest[1].querySelector("a").href.split("/")[4];
        let is_rated = (contest[5].getAttribute("data-search") == "[RATED]");

        if(is_rated){
            // Unratedコンテストの新Ratingの箇所を埋めたい場合はコメントを外す
            // rating = contest[4].innerText;
            continue;
        }

        if(userperfs[contest_name] !== undefined) contest[3].innerText = userperfs[contest_name];

        // Unratedコンテストの新Ratingの箇所を埋めたい場合はコメントを外す その2
        // contest[4].innerText = rating;
    }
    return;
}

async function displayperf_competition_history(){
    if(document.querySelector("a.username span") === null) return;

    let username = document.querySelector("a.username span").innerText;
    let url = "https://new-textfile.github.io/AtCoderUnratedPerformances/userperfs/" + username + ".json";

    //Unratedコンテストのパフォーマンス推定値一覧をlocalStorageまたはgithubから取得
    let userperfs = JSON.parse(localStorage.getItem("AtCoderUnratedPerfDisplayer-" + username));
    if(userperfs === null){
        let userperfs_html = await fetch(url);

        //fetchに失敗したら何もせず終了(1回もUnrated参加していないなどの場合に起こり得る)
        if(!userperfs_html.ok) return;
        userperfs = await (userperfs_html).json();

        //他のuserscriptとの兼ね合いもあるため, localStorageに保存する
        localStorage.setItem("AtCoderUnratedPerfDisplayer-" + username, JSON.stringify(userperfs));
    }

    //userperfsを参照して, コンテスト成績表のパフォーマンスの列を書き換える
    displayperf(userperfs);

    //github上にあるパフォーマンス一覧を取得
    await new Promise(resolve => setTimeout(resolve, 1000)); //sleep (1000ms)
    let remote_userperfs_html = await fetch(url);
    if(!remote_userperfs_html.ok) return; //fetchに失敗したら何もせず終了
    let remote_userperfs = await (remote_userperfs_html).json();

    //github上とlocalStorageでパフォーマンス一覧が異なる場合, localStorageの値をgithub上の値で上書きする
    let remote_userperfs_json = JSON.stringify(Object.keys(remote_userperfs).sort());
    let userperfs_json = JSON.stringify(Object.keys(userperfs).sort());
    if(remote_userperfs_json !== userperfs_json){
        localStorage.setItem("AtCoderUnratedPerfDisplayer-" + username, JSON.stringify(remote_userperfs));

        //github上のuserperfsを参照して, コンテスト成績表のパフォーマンスの列を書き換える
        displayperf(remote_userperfs);
    }

}

async function displayperf_contest_result(){
    if(document.querySelector("table a.username span") === null) return;

    let username = document.querySelector("table a.username span").innerText;
    let contest = document.querySelectorAll("table tr")[1].querySelector("a");
    let contest_name = contest.href.split("/")[4];

    //Unratedコンテストのパフォーマンス推定値一覧をlocalStorageまたはgithubから取得
    let userperfs = JSON.parse(localStorage.getItem("AtCoderUnratedPerfDisplayer-" + username));
    if(userperfs === null){
        let url = "https://new-textfile.github.io/AtCoderUnratedPerformances/userperfs/" + username + ".json";

        let userperfs_html = await fetch(url);
        if(!userperfs_html.ok) return; //fetchに失敗したら何もせず終了
        userperfs = await (await fetch(url)).json();
    }

    if(userperfs[contest_name] !== undefined){
        //コンテスト成績証にパフォーマンスの行を追加
        add_perfrow(userperfs[contest_name]);

        //twitterの共有ボタンのツイートメッセージを変更
        change_tweetmsg(userperfs[contest_name]);
    }
}

function add_perfrow(perf){
    let lang = document.head.querySelectorAll("meta")[1].content;

    let innerHTML_str = "";
    innerHTML_str += "<th class=\"no-break\">";
    innerHTML_str += (lang == "ja" ? "パフォーマンス(推定)" : "Performance(Estimated)");
    innerHTML_str += "</th>\n<td><span class=\"user-" + perf2color(perf) +"\">" + perf + "</span></td>";

    document.querySelector("table").insertAdjacentHTML("beforeend", innerHTML_str);
}

function change_tweetmsg(perf){
    //言語設定(ja/en)
    let lang = document.head.querySelectorAll("meta")[1].content;

    //元のツイートメッセージ(の一部)
    let textlist = document.querySelector("div.a2a_kit").attributes[2].textContent.split("\n");

    let text = "";
    for(let rownum in textlist){
        text += textlist[rownum] + "\n";

        //元のツイートメッセージの1行目と2行目の間にパフォーマンスの行を追加
        if(rownum == 0){
            if(lang == "ja") text += "パフォーマンス(推定)：" + perf + "相当\n";
            else text += "Performance(Estimated): " + perf + "\n";
        }
    }

    document.querySelector("div.a2a_kit").setAttribute("data-a2a-title", text);
}

function perf2color(perf){
    let perf_num = Number(perf);
    let res = "";

    if(perf_num < 400) res = "gray";
    else if(perf_num < 800) res = "brown";
    else if(perf_num < 1200) res = "green";
    else if(perf_num < 1600) res = "cyan";
    else if(perf_num < 2000) res = "blue";
    else if(perf_num < 2400) res = "yellow";
    else if(perf_num < 2800) res = "orange";
    else res = "red";

    return res;
}