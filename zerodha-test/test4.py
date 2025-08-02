import asyncio
import aiohttp
import pyotp
import requests
from datetime import datetime, time

# --- Credentials ---
KITE_USERNAME = "your_user_id"
KITE_PASSWORD = "your_password"
TOTP_KEY = "your_totp_secret"

# --- Globals ---
enctoken = None  # will be updated after login

# --- Login Function ---
def login_kite():
    global enctoken
    session = requests.Session()

    res1 = session.post(
        'https://kite.zerodha.com/api/login',
        data={
            "user_id": KITE_USERNAME,
            "password": KITE_PASSWORD,
            "type": "user_id"
        }
    )
    request_id = res1.json()['data']['request_id']

    res2 = session.post(
        'https://kite.zerodha.com/api/twofa',
        data={
            "request_id": request_id,
            "twofa_value": pyotp.TOTP(TOTP_KEY).now(),
            "user_id": KITE_USERNAME,
            "twofa_type": "totp"
        }
    )
    enctoken = session.cookies.get_dict()['enctoken']
    print("Login completed at:", datetime.now())


# --- Async Order Placement ---
async def place_order(session, order):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://kite.zerodha.com/dashboard",
        "Accept-Language": "en-US,en;q=0.6",
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"enctoken {enctoken}"
    }
    url = 'https://kite.zerodha.com/oms/orders/regular'
    async with session.post(url, headers=headers, data=order) as response:
        r = await response.json()
        print(f"Order {order['tradingsymbol']} => {r}")


# --- Main Runner ---
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [place_order(session, order) for order in orders]
        await asyncio.gather(*tasks)


# --- Scheduler Loop ---
def schedule_loop():
    print("Waiting for 09:14:00 to login...")
    while datetime.now().time() < time(9, 14, 0, 0):
        continue
    login_kite()

    print("Waiting for 09:15:00 to place orders...")
    while datetime.now().time() < time(9, 15, 0, 0):
        continue
    asyncio.run(main())


# --- Hardcoded Orders List ---
orders = [
    {
        "variety": "regular",
        "exchange": "NSE",
        "tradingsymbol": "NIFTYBEES",
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "quantity": 10,
        "price": 232.50,
        "product": "MIS",
        "validity": "TTL",
        "validity_ttl": "1",
        "user_id": KITE_USERNAME
    },
    {
        "variety": "regular",
        "exchange": "NSE",
        "tradingsymbol": "BANKBEES",
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "quantity": 5,
        "price": 584.80,
        "product": "MIS",
        "validity": "TTL",
        "validity_ttl": "1",
        "user_id": KITE_USERNAME
    },
    {
        "variety": "regular",
        "exchange": "NSE",
        "tradingsymbol": "ITBEES",
        "transaction_type": "SELL",
        "order_type": "LIMIT",
        "quantity": 8,
        "price": 355.25,
        "product": "MIS",
        "validity": "TTL",
        "validity_ttl": "1",
        "user_id": KITE_USERNAME
    }
]

# --- Start ---
if __name__ == "__main__":
    schedule_loop()

