import datetime as dt

import telegram
import yfinance as yf
import base64


def _is_xetra_holiday(d: dt.date):
    xetra_holidays = [dt.date(2020, 12, 24),
                      dt.date(2020, 12, 25),
                      dt.date(2020, 12, 31),
                      dt.date(2021, 1, 1),
                      dt.date(2021, 4, 2),
                      dt.date(2021, 4, 5),
                      dt.date(2021, 5, 24),
                      dt.date(2021, 12, 25),
                      dt.date(2021, 12, 31)]
    return d in xetra_holidays or d.isoweekday() > 5


def change(yesterday_close, today_close):
    ret = 100 * (today_close / yesterday_close - 1)
    ret_f = '%.2f' % ret
    today_close_f = '%.2f' % round(today_close, 2)
    sign = '+' if ret > 0 else ''
    return f'{today_close_f} ({sign}{ret_f}%)'


def extract_md(t):
    ticker = yf.Ticker(t)
    close_ts = ticker.history(period='1mo', rounding=False).Close
    yesterday_close, today_close = close_ts.iloc[-2:]
    return f'{t} ' + change(yesterday_close, today_close)


def db_market_data():
    if _is_xetra_holiday(dt.date.today()):
        raise Exception('today is a xetra holiday')
    return extract_md('DBK.DE')


def send_to_telegram(text, set_title=False):
    import os
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    bot = telegram.Bot(token=token)
    if set_title:
        print(f'setting telegram chat title to {text}')
        resp = bot.set_chat_title(chat_id, text)
        print(resp)
    else:
        print(f'sending to telegram chat {text}')
        resp = bot.send_message(chat_id, text)
        print(resp)


def send_xetra():
    try:
        text = db_market_data()
        send_to_telegram(text, set_title=True)
        return "xetra market data published"
    except Exception as inst:
        return inst


def send_lse():
    try:
        text = extract_md('BARC.L')
        send_to_telegram(text, set_title=False)
        return "lse market data published"
    except Exception as inst:
        return inst


def send_nyse():
    try:
        text = extract_md('C')
        send_to_telegram(text, set_title=False)
        return "nyse market data published"
    except Exception as inst:
        return inst


def send_nasdaqgs():
    try:
        #text = extract_md('YNDX')
        #send_to_telegram(text, set_title=False)
        return "nasdaq market data published"
    except Exception as inst:
        return inst


def send_euronext():
    try:
        text = extract_md('BNP.PA')
        send_to_telegram(text, set_title=False)
        return "euronext market data published"
    except Exception as inst:
        return inst


def market_data(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(f"processing {pubsub_message}")
    if (pubsub_message == 'XETRA'):
        return send_xetra()
    elif (pubsub_message == 'NYSE'):
        return send_nyse()
    elif (pubsub_message == 'NASDAQGS'):
        return send_nasdaqgs()
    elif (pubsub_message == 'EURONEXT'):
        return send_euronext()
    elif (pubsub_message == 'LSE'):
        return send_lse()
    else:
        return f"unknown exchange: {pubsub_message}"
