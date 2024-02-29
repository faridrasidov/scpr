import concurrent.futures
import time, requests, os, datetime
import telebot
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Loading specified data from ".env" file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ID = os.getenv("TELEGRAM_ID")
SLEEP_TIME = int(os.getenv("SLEEP_TIME"))
START = os.getenv("START")
ERROR = os.getenv("ERROR")
SMS_0_API = os.getenv("SMS_0_API")
SMS_0 = os.getenv("SMS_0")
SMS_0_FUNC = os.getenv("SMS_0_FUNC")
SMS_1_API = os.getenv("SMS_1_API")
SMS_1 = os.getenv("SMS_1")
SMS_1_FUNC = os.getenv("SMS_1_FUNC")
SMS_1_TEL = os.getenv("SMS_1_TEL")

# Some Func to Send Notify in Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN)
def Telegram_Send(number, tiem, todo):
    chat_id = TELEGRAM_ID
    url = f"{SMS_1_TEL}{todo}&csrf="
    link = f"<i>To see InBox</i> <a href=\"{url}\"><b>Click Here</b></a>"
    message = f"<i>Number:</i> <code>+{number}</code>\n<i>Added: {tiem}</i>" + "\n" + link
    bot.send_message(chat_id, message, parse_mode='HTML')

# Gets Time By "City"
def NowTime(City):
    Base = {
        "Msk": 3
    }
    try :
        if City in Base:
            offset = datetime.timedelta(hours=Base[City])
            utc_time = datetime.datetime.utcnow()
            t = utc_time + offset
            return t
    except Exception:
        pass


# Write Text to (.log) File Or Clear File
def Writing_L0G(func, elem='', req='a'):
    funcs = [SMS_0_FUNC, SMS_1_FUNC]
    if func in funcs:
        with open(func + 'logs.log', req) as file:
            if req == "a":
                file.write(elem + '\n')
            elif req == "w":
                file.write('')


# Gets Country List From SMS_0
def Find_Country_SMS_0():
    Func = SMS_0_FUNC
    Sms0Cntrylist = []
    try:
        response = requests.get(f"{SMS_0}")
        data = response.json()
        for item in data['data']['countries']:
            Sms0Cntrylist.append(item['id'] + ":" + item['code'])
    except Exception as e:
        Writing_L0G(Func, ERROR)
        Writing_L0G(Func, f"{e}")
    return Sms0Cntrylist


# Finds When Numbers Added [SMS_0]
def Find_Delay_SMS_0():
    Func = SMS_0_FUNC
    while True:
        Sms0Contry = Find_Country_SMS_0()
        Writing_L0G(Func, START)
        for item in Sms0Contry:
            GText = item.split(":")
            api = f"{SMS_0_API}{GText[0]}&asc=getAvailablePhonesForCountry&csrf="
            response = requests.get(api)
            try:
                data = response.json()
                numbers = [entry['phone'] for entry in data['data']]
                create_dates = [entry['createDate'] for entry in data['data']]
                num_id = [entry['id'] for entry in data['data']]
                GTextLen = len(GText[1])
                current_time = NowTime("Msk")
                diff_text = []
                diff_check = []
                for create_date in create_dates:
                    create_date_time = datetime.datetime.strptime(create_date, "%Y-%m-%d %H:%M:%S")
                    time_difference = current_time - create_date_time
                    seconds = time_difference.total_seconds()
                    formatted_difference = f"{int(seconds // 86400)} days " \
                                           f"{str(datetime.datetime.utcfromtimestamp(seconds).strftime('%H:%M'))}"
                    diff_text.append(formatted_difference)
                    diff_check.append(seconds)
                for num, cd, rcd, sec, di in zip(numbers, create_dates, diff_text, diff_check, num_id):
                    if sec < 600:
                        Telegram_Send(num, rcd, di)
                    numlen = 13 - len(num)
                    Writing_L0G(Func,
                                f"\033[92m+{GText[1]}\033[0m" + num[GTextLen:] + ' ' * numlen + " | " + cd[5:] + " | " + rcd)
            except Exception as e:
                Writing_L0G(Func, ERROR)
                Writing_L0G(Func, f"{e}")
        time.sleep(SLEEP_TIME)
        Writing_L0G(Func, req="w")


# Gets Country List From SMS_0
def Find_Country_SMS_1(func=None):
    if func is None:
        func = []
    Func = SMS_1_FUNC
    Countries = []
    Conarchive = []
    try:
        if len(func) == 0:
            Deal = SMS_1
            tosearch = "countries"
        else:
            Deal = func
            tosearch = "fw-items"

        response = requests.get(Deal)
        parsresponse = BeautifulSoup(response.content, 'html.parser')
        List = parsresponse.find(class_=tosearch)
        A_List = List.find_all("a")
        for element in A_List:
            cntryresponse = BeautifulSoup(str(element), 'html.parser')
            numlink = cntryresponse.a['href']
            Countries.append(numlink)
            archNumbs = cntryresponse.find_all(class_='--archive')
            for ele in archNumbs:
                archresponse = BeautifulSoup(str(ele), 'html.parser')
                archs = archresponse.a['href']
                Conarchive.append(archs)

    except Exception as e:
        Writing_L0G(Func, ERROR)
        Writing_L0G(Func, f"{e}")
    SLT = [rl for rl in Countries if rl not in Conarchive]
    if len(func) == 0:
        Countries = []
        for elem in SLT:
            tip = SMS_1 + elem
            mod_tip = tip.replace(" ", '%20')
            Countries.append(mod_tip)
        return Countries
    else:
        SALT = [element.replace('/free_numbers', '') for element in SLT]
        return SALT


# Finds When Numbers Added [SMS_1]
def Find_Delay_SMS_1():
    Func = SMS_1_FUNC
    while True:
        Writing_L0G(Func, START)
        CounRit = Find_Country_SMS_1()
        ThreatNums = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fnd = {executor.submit(Find_Country_SMS_1, url): url for url in CounRit}
            for future in concurrent.futures.as_completed(fnd):
                bnd = future.result()
                ThreatNums += bnd
        Links = []
        try:
            for count in ThreatNums:
                flink = f"{SMS_1_API}{count}?page=1&count=100&ui=true&lang=en"
                response = requests.get(flink)
                data = response.json()
                Links.append(data['messages']['total'])
                w = count.split("/")
                char = 15 - len(w[-1])
                totala = str(data['messages']['total'])
                code = str(data['code'])
                codeLen = len(code)
                if int(totala) < 100:
                    Telegram_Send(code + w[-1][codeLen:], totala, "-")
                Writing_L0G(Func, str("+" + f"\033[92m{code}\033[0m" + w[-1][codeLen:]) + " " * char +
                            "| " + f"\033[92m{totala}\033[0m")
                time.sleep(0.5)
        except Exception as e:
            Writing_L0G(Func, ERROR)
            Writing_L0G(Func, f"{e}")
        time.sleep(SLEEP_TIME)
        Writing_L0G(Func, req="w")


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exctr:
    stCycle = exctr.submit(Find_Delay_SMS_0)
    ndCycle = exctr.submit(Find_Delay_SMS_1)
