from datetime import datetime, timedelta
from datetime import date, datetime
import requests
import holidays
import time
import json
from bs4 import BeautifulSoup

import dotenv
from telegram_notifier import Notifier

dotenv.load_dotenv()
notifier = Notifier()

TARGET_URL = "https://www.tge.pl/energia-elektryczna-rdn?dateShow=DATEHERE"  # Replace with your target site
FETCH_TIME = {"hour": 14, "minute": 1}  # Fetch every day at 14:01
fetched_today = False

def calcprice(row, dt):
    G13_LOW = 0.0349
    G13_MED = 0.1883
    G13_HIGH = 0.3332
    winter = dt.month>=10 and dt.month <=3
    hour, price = row
    price=price/1000+0.0892
    if dt.weekday()>4 or dt in holidays.PL(): price+=G13_LOW
    else:
        if hour>=7 and hour<13: price+=G13_MED
        else:
            if winter:
                if hour>=16 and hour<21: price+=G13_HIGH
                else: price+=G13_LOW
            else:
                if hour>=19 and hour<22: price+=G13_HIGH
                else: price+=G13_LOW
    price += 0.03210 # stawka jakościowa
    price += 0.00350 # opłata OZE
    price += 0.00300 # opłata kogeneracyjna
    price *= 1.23
    return [hour, price]

def fetch_site():
    global fetched_today
    try:
        today = date.today()
        now = datetime.now()
        if now.hour > 13 or (now.hour == 13 and now.minute >= 50):
            today += timedelta(days=1)
        formatted_date = today.strftime("%d-%m-%Y")
        url = TARGET_URL.replace("DATEHERE", formatted_date)
        print(f"Fetching site content from url {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        realdate_tag='dla dostawy w dniu '
        realdate=html[html.find(realdate_tag)+len(realdate_tag):]
        realdate=realdate[:realdate.find('<')]
        assert realdate==formatted_date
        rows = soup.find_all('tr')
        table_data = []
        for row in rows:
            cells = row.find_all('td')
            row_data = []
            for cell in cells[:2]:
                text = cell.get_text(strip=True)
                row_data.append(text)
            if row_data:
                table_data.append(row_data)
        data = [calcprice((int(row[0][:row[0].find('-')]), float(row[1].replace(',', '.').replace(' ', ''))), today) for row in table_data if row[0][0].isdigit() and '-' in row[0] and row[0][-1].isdigit()]
        # print(data)
        msg = realdate+"\n"
        for v in data:
            hr=str(v[0])+":00"
            if len(hr)==1: hr='0'+hr
            msg+=hr+" "+str(round(v[1], 3))+"\n"
        notifier.send_message(msg)
        fetched_today=True
    except requests.RequestException as e:
        print(f"Error fetching site: {e}")
        fetched_today=False
        time.sleep(300)


def schedule_fetch():
    while True:
        now = datetime.now()
        target_time = now.replace(
            hour=FETCH_TIME["hour"], minute=FETCH_TIME["minute"], second=0, microsecond=0
        )
        print(now, target_time, fetched_today)
        if now > target_time and fetched_today:  # If today's fetch time has passed, schedule for tomorrow
            target_time += timedelta(days=1)
        time_until_fetch = (target_time - now).total_seconds()
        
        print(f"Next fetch scheduled at: {target_time}")
        if time_until_fetch>0: time.sleep(time_until_fetch)  # Wait until the next fetch time
        fetch_site()  # Perform the fetch


if __name__ == "__main__":
    schedule_fetch()
