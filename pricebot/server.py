from datetime import datetime, timedelta
from datetime import date, datetime
import requests
import holidays
import time
import json

import dotenv
from telegram_notifier import Notifier

dotenv.load_dotenv()
notifier = Notifier()

TARGET_URL = "https://energy-api.instrat.pl/api/prices/energy_price_rdn_hourly?date_from=DATEHERET00:00:00Z&date_to=DATEHERET23:59:00Z"  # Replace with your target site
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
        content = json.loads(response.text)
        if len(content)!=24: raise Exception(f"Content len is {len(content)}") 
        data=[(i, val['fixing_i']['price']) for i, val in enumerate(content)]
        data = [calcprice(row, today) for row in data]
        print(data)
        msg = formatted_date+"\n"
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
