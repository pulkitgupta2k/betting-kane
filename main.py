import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from selenium import webdriver

PLACE_FACTION = 5
BF_COMMISSION = 5
EW_STAKE = 100

def getSoup(link):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
               "Content-Type": "text/html;charset=UTF-8"}

    req = requests.get(link, headers=headers)
    html = req.content
    # with open("test.html", "w", encoding="utf-8") as f:
    #     f.write(req.text)
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def betfair_race(link):
    soup = getSoup(link)
    data = {}
    rows = soup.findAll("tr", {"class": "runner-body"})
    for row in rows:
        runner = row.find("td", {"class": "runner"}).find(
            "span", {"class": "runner-name-value"})['title']
        try:
            odd = float(row.find("td", {"class": "win-sp"}
                                 ).find("span", {"class": "ui-runner-price"}).text.strip())
        except:
            odd = None
        data[runner] = {"win": odd}

    link = link + "&action=loadRacecardTab&racecardTabType=PLACE&modules=racecard%401004&marketType=PLACE"
    soup = getSoup(link)
    rows = soup.findAll("tr", {"class": "runner-body"})
    for row in rows:
        runner = row.find("td", {"class": "runner"}).find(
            "span", {"class": "runner-name-value"})['title']
        try:
            odd = float(row.find("td", {"class": "column-bet-button"}
                                 ).find("span", {"class": "ui-runner-price"}).text.strip())
        except:
            odd = None
        data[runner]["place"] = odd
    
    # for key, value in data.items():
    #     try:
    #         data[key]["eff_place_ratio"] = (win-1)/PLACE_FACTION+1
    #         data[key]["lay_win"] = (EW_STAKE*win)/(win-BF_COMMISSION)

    #     except:
    #         data[key]["eff_place_ratio"] = None
    #         data[key]["lay_win"] = None
    return data


def betfair():
    soup = getSoup("https://www.betfair.com/sport/horse-racing?filter=ALL")
    race_window = soup.find("div", {"class": "races-window"})
    races = {}
    for race in race_window.findAll("div", {"class": "race-view"}):
        name = race.find("a")['data-galabel']
        link = "https://www.betfair.com" + race.find("a")['href']
        races[name] = {"runners": betfair_race(link), "link": link}

    with open("data.json", "w") as f:
        json.dump(races, f)


def bet365(driver):
    driver.get("https://www.bet365.com/#/AS/B2/")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    races = {}
    aus_races = soup.findAll("div", {"class": "rsm-AusRacingSplashScroller "})
    for race in aus_races:
        name = race.find("div", {
                         "class": "rsm-AusMeetingHeader_MeetingName rsm-AusMeetingHeader_MeetingName-link "}).text
        times = race.findAll(
            "div", {"class": "rsm-AusRacingSplashParticipant_Countdown "})
        for time in times:
            key = ":".join(time.text.replace("h", "").replace("m", "").split())
            print(key+" "+name)


if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/74.0.3729.169 Safari/537.36')
    driver = webdriver.Chrome('./chromedriver', options=options)
    
    # driver.add_cookie({'name': 'aps03', 'value': 'cf=N&cg=3&cst=0&ct=198&hd=N&lng=32&oty=2&tzi=2', 'sameSite': 'Lax'})
    bet365(driver)
    # betfair()
    # link = "https://www.betfair.com/sport/horse-racing/meeting?eventId=30481349&raceTime=1620141600000&dayToSearch=20210504&marketId=924.262961570"
    # betfair_race(link)
