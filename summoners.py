# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
import urllib
from urllib import parse
from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template
app = Flask(__name__)
slack_token = "xoxb-508876955558-508878795382-fZbzfSBHm1MLK1WftHjj5YIz"
slack_client_id = "508876955558.507475670354"
slack_client_secret = "a7d8661f06f95c52d437b130e12b5480"
slack_verification = "1NWEFeHmYb08eKgBFN5TkXej"
sc = SlackClient(slack_token)
# 크롤링 함수 구현하기
def _crawl_opgg(text):
    if "help" in text:
        string = "@summoners 봇 명령어 소개 (소문자로 작성하셔야 합니다)\ndefault : @summoners _command_소환사 명\n<command>\ninfo : 소환사 기본 정보\npastrank : 과거 시즌 티어 정보\nmostchamp : 현재 시즌 모스트 챔피언\n7days : 최근 7일간 게임 전적\n"
        return string
    text = text.split("_")
    if 3 != len(text):
        string = "사용할 수 없는 명령어입니다. 참고 @summoners help"
        return string
    com = text[1]
    name = text[2]
    url = "http://www.op.gg/summoner/userName=" + parse.quote(name)
    req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    if "pastrank" in com:
        pRank = []
        for past in soup.find("ul", {"class": "PastRankList"}).find_all("li", recursive=False):
            pRank.append(past.get_text().strip())
        pRank = '\n'.join(pRank)
        string = str(name) + "님의 과거 랭크 ↓↓↓ \n" + str(u''.join(pRank))
        return string
    elif "mostchamp" in com:
        champs = []
        try:
            for champ in soup.find("div", {"class": "MostChampionContent"}).find_all("div", class_="ChampionInfo"):
                if 5 > len(champs):
                    champs.append(
                        champ.get_text().replace("\n", "").replace("\t", "").replace(")", ")\n").replace("CS", " CS"))
        except AttributeError as e:
            string = str(name) + "님은 현재 시즌 게임을 플레이하지 않았습니다"
            return string
        string = str(name) + "님의 모스트 5 챔피언 ↓↓↓\n" + str(u''.join(champs))
        return string
    elif "check" in com:
        check_state = []
        check_state = soup.find_all("th", class_="HeaderCell.TeamName")
        if "블루팀" in check_state:
            string = str(name) + "님은 현재 게임중입니다."
            return string
        else:
            string = str(name) + "님은 현재 게임중이 아닙니다."
            return string
    elif "info" in com:
        words = []
        result = []
        for rank in soup.find_all("span", class_="tierRank"):
            words.append(rank.get_text().strip())
            if 'Unranked' in words:
                result.append('현재 티어: ' + str(words[0]))
            else:
                for point in soup.find_all("span", class_="LeaguePoints"):
                    words.append(point.get_text().strip())
                for win in soup.find_all("span", class_="wins"):
                    words.append(win.get_text().strip())
                for loss in soup.find_all("span", class_="losses"):
                    words.append(loss.get_text().strip())
                for league in soup.find_all("div", class_="LeagueName"):
                    words.append(league.get_text().strip())
                result.append(('현재 티어 : ' + str(words[0]) + '\n리그 포인트 : ' + str(words[1]) + '\n' + str(words[2]) + ' / ' + str(words[3]) + '\n리그 : ' + str(words[4])))
        string = str(name) + "님의 정보 ↓↓↓\n" + str(u''.join(result))
        return string
    elif "7days" in com:
        string = str(name) + "님의 최근 7일간 랭크 승률\n"
        list_name = []
        list_ratio = []
        list_win = []
        list_lose = []
        for h in soup.find_all("div", class_="ChampionWinRatioBox"):
            ratio = h.find("div", class_="WinRatio").get_text().split()
            list_ratio.append(ratio[0])
            namelink = h.find("a")["href"].split('/')[2]
            list_name.append(namelink)
            winlose = h.find("div", class_="Graph").get_text().split()
            if len(winlose) == 2:
                list_win.append(winlose[0])
                list_lose.append(winlose[1])
            else:
                winlose = winlose[0]
                if 'W' == winlose[-1]:
                    list_win.append(winlose)
                    list_lose.append('0L')
                else:
                    list_lose.append(winlose)
                    list_win.append('0W')
        if len(list_name) == 0:
            string += "최근 7일동안 랭크 게임을 하지 않았습니다.\n"
        else:
            for i in range(0, len(list_name)):
                string += str(i + 1) + '. ' + list_name[i] + '\n   ' + list_win[i] + '/' + list_lose[i] + ' 승률 : ' + \
                          list_ratio[i] + '\n'
        return string
    else:
        return "사용할 수 없는 명령입니다."
# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])
    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]
        keywords = _crawl_opgg(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )
        return make_response("App mention message has been sent", 200, )
    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})
@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })
    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"
if __name__ == '__main__':
    app.run('127.0.0.1', port=5000)
