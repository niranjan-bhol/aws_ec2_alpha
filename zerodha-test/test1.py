import requests
import pyotp

# --- Credentials ---
KITE_USERNAME = ''
KITE_PASSWORD = ''
TOTP_KEY = ''

def kite_login(username, password, totp_key):
    session = requests.Session()

    res1 = session.post(
        'https://kite.zerodha.com/api/login',
        data={"user_id": username, "password": password, "type": "user_id"}
    )
    login_data = res1.json()['data']

    totp = pyotp.TOTP(totp_key).now()
    res2 = session.post(
        'https://kite.zerodha.com/api/twofa',
        data={
            "request_id": login_data['request_id'],
            "twofa_value": totp,
            "user_id": login_data['user_id'],
            "twofa_type": "totp"
        }
    )

    return session.cookies.get_dict()['enctoken']

def place_order(enctoken, order_data):
    url = 'https://kite.zerodha.com/oms/orders/regular'
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://kite.zerodha.com/dashboard",
        "Accept-Language": "en-US,en;q=0.6",
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"enctoken {enctoken}"
    }

    res = requests.post(url, headers=headers, data=order_data)
    return res.json()

# --- Run ---
enctoken = kite_login(KITE_USERNAME, KITE_PASSWORD, TOTP_KEY)

order_data = {
    "variety": "regular",
    "exchange": "NSE",
    "tradingsymbol": "IEX",
    "transaction_type": "BUY",
    "order_type": "LIMIT",
    "quantity": 1,
    "price": 221,
    "product": "CNC",
    "validity": "DAY",
    "disclosed_quantity": 0,
    "trigger_price": 0,
    "squareoff": 0,
    "stoploss": 0,
    "trailing_stoploss": 0,
    "user_id": KITE_USERNAME
}

response = place_order(enctoken, order_data)
print(response)
