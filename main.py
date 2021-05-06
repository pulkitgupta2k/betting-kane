import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from selenium import webdriver
from datetime import datetime
import time
import csv 
import itertools 

PLACE_FACTION = 5
BF_COMMISSION = 5/100
EW_STAKE = 100


def getSoup(link):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
               "Content-Type": "text/html;charset=UTF-8"}

    req = requests.get(link, headers=headers)
    html = req.content
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def betfair():
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome('./chromedriver', options=options)
    link = "https://www.betfair.com.au/exchange/plus/en/horse-racing-betting-7"
    driver.get(link)
    while True:
        try:
            driver.find_element_by_xpath("//section[@class='mod-todays-racing']")
            break
        except:
            pass
    races = {}
    # print(len(driver.find_elements_by_class_name('tab-wrapper')))
    for page in driver.find_elements_by_class_name('tab-wrapper'):
        page.click()
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        meeting_items = soup.findAll("li", {"class": "meeting-item"})
        for item in meeting_items:
            location = item.find(
                "div", {"class": "meeting-info"}).find("div", {"class": "meeting-label"}).text
            # print(location)
            for race in item.findAll("li", {"class": "race-information"}):
                link = "https://www.betfair.com.au/exchange/plus/"+race.find("a")["href"]
                t = race.find("span", {"class": "label"}).text
                name = t + " " + location
                races[name] = {"link_bf": link}

    with open("data.json", "w") as f:
        json.dump(races, f)


def sportsbet():
    with open('data.json') as f:
        data = json.load(f)
    new_data = {}
    soup = str(getSoup("https://www.sportsbet.com.au/racing-schedule/horse/today").findAll(
        "script")[-4]).split("window.__")[1].replace("PRELOADED_STATE__ = ", "")
    soup = json.loads(soup)
    # with open("sportsbet.json", "w") as f:
    #     json.dump(soup, f)
    competitions = soup['entities']['sportsbook']['competitions']
    events = soup['entities']['sportsbook']['events']
    for key, value in events.items():
        class_id = competitions[str(value['competitionId'])]['classId']
        if class_id == 1 or class_id == 2:
            pass
        else:
            continue
        if class_id == 1:
            location = "australia-nz"
            sec = 16200
        if class_id == 2:
            location = "international"
            sec = 16200
        name = competitions[str(value['competitionId'])]['name']
        if value['startTime']['milliseconds']/1000 <= float(datetime.now().timestamp()):
            continue
        time = datetime.fromtimestamp(
            value['startTime']['milliseconds']/1000+sec).strftime('%H:%M')
        
        link = f"https://www.sportsbet.com.au/horse-racing/{location}/{'-'.join(name.split())}/race-{str(value['raceNumber'])}-{key}"
        name = time + " " + name
        # print(name)
        # data[name] = {"link_sportsbet": link}
        if name in data.keys():
            new_data[name] = data[name]
            data[name]["link_sportsbet"] = link
    with open("data.json", "w") as f:
        json.dump(new_data, f)


def betfair_race(link, driver):
    driver.get(link)
    runners = {}
    time.sleep(2)
    for i in range(3):
        try:
            driver.find_element_by_xpath("//div[@class='markets-tabs-container']")
        except:
            time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.find_element_by_xpath("//a[@title='Place']").click()
    # driver.get("https://www.betfair.com.au/exchange/plus/" + soup.find("a", {"title": "Place"})['href'] )

    for runner in soup.findAll("tr", {"class": "runner-line"}):
        name = runner.find("h3", {"class": "runner-name"}).contents[0]
        try:
            odd = float(runner.findAll("button", {"class": "lay-button"})[0].find("span", {"class": "bet-button-price"}).text)
        except:
            continue
        runners[name] = {"win_bf": odd}
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for runner in soup.findAll("tr", {"class": "runner-line"}):
            name = runner.find("h3", {"class": "runner-name"}).contents[0]
            try:
                odd = float(runner.findAll("button", {"class": "lay-button"})[0].find("span", {"class": "bet-button-price"}).text)
            except:
                continue
            runners[name]["place_bf"] = odd

    # print(runners)
    # palce_soup = BeautifulSoup(driver.page_source, "html.parser")
    return runners


def sportsbet_race(link):
    soup = str(getSoup(link).findAll("script")
               [-4]).split("window.__")[1].replace("PRELOADED_STATE__ = ", "")
    soup = json.loads(soup)
    runners = {}
    for key, value in soup['entities']['sportsbook']['outcomes'].items():
        name = value['name']
        try:
            odd = value['recentOddsFluctuations'][0]
        except:
            continue
        runners[name] = {'win_spbt': odd}
    return runners


def driver():
    with open("data.json") as f:
        data = json.load(f)
    data = dict(sorted(data.items()))
    data = dict(itertools.islice(data.items(), 10))
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument("--log-level=3")
    sel_driver = webdriver.Chrome('./chromedriver', options=options)

    for key, value in data.items():
        runners = sportsbet_race(value['link_sportsbet'])
        try:
            runners1 = betfair_race(value['link_bf'], sel_driver)
        except:
            runners1 = {}
            pass
        if runners1 == None:
            runners1 = {}
        for key1, value1 in runners1.items():
            if key1 in runners.keys():
                runners[key1].update(value1)

        data[key]['runners'] = runners
    
    runners = []
    runners.append(["NAME", "LINK", "SPORTSBET ODDS", "BETFAIR WIN", "BETFAIR PLACE", "EFF PLACE ODDS", "LAY ON WIN", "LAY ON PLACE", "PROFIT WIN", "PROFIT PLACE", "NET PROFIT"])
    for key, value in data.items():
        for name, runner in value['runners'].items():
            if "win_bf" not in runner.keys():
                continue
            if runner["win_bf"] == 0 or runner["place_bf"] == 0:
                continue
            eff = round((runner["win_spbt"]-1)/PLACE_FACTION+1, 2)
            lay_win = round((EW_STAKE*runner["win_spbt"])/(runner["win_bf"]-BF_COMMISSION),2)
            lay_place = round((EW_STAKE*eff)/(runner["place_bf"] - BF_COMMISSION),2)
            profit_win = round((1-BF_COMMISSION)*lay_win-EW_STAKE,2)
            profit_place = round((1-BF_COMMISSION)*lay_place-EW_STAKE,2)
            net_profit = round(profit_win + profit_place,2)
            runners.append([name,value['link_bf'] ,runner["win_spbt"], runner["win_bf"], runner["place_bf"], eff, lay_win, lay_place, profit_win, profit_place, net_profit, ])
    try:
        with open("runners.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(runners)
    except:
        print("Close the spreadsheet please and press enter")
        a = input()
        with open("runners.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(runners)

    with open("data.json", "w") as f:
        json.dump(data, f)


if __name__ == "__main__":

    betfair()
    sportsbet()
    driver()
