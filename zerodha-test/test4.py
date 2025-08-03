import requests
import pyotp
import aiohttp
import asyncio

# --- Credentials ---
KITE_USERNAME = 'DXU151'
KITE_PASSWORD = 'Pratibha'
TOTP_KEY = 'FLJBDJNEBOIMZZZPE25YYYR72Y2B2IAP'

# --- Login Function (sync) ---
def kite_login(username, password, totp_key):
    session = requests.Session()

    res1 = session.post(
        'https://kite.zerodha.com/api/login',
        data={"user_id": username, "password": password, "type": "user_id"}
    )
    login_data = res1.json()['data']

    totp = pyotp.TOTP(totp_key).now()
    session.post(
        'https://kite.zerodha.com/api/twofa',
        data={
            "request_id": login_data['request_id'],
            "twofa_value": totp,
            "user_id": login_data['user_id'],
            "twofa_type": "totp"
        }
    )

    return session.cookies.get_dict()['enctoken']

# --- Async Order Placement ---
async def place_order_async(session, enctoken, order_data):
    url = 'https://kite.zerodha.com/oms/orders/regular'
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://kite.zerodha.com/dashboard",
        "Accept-Language": "en-US,en;q=0.6",
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"enctoken {enctoken}"
    }

    async with session.post(url, headers=headers, data=order_data) as resp:
        return await resp.json()

# --- Main Async Executor ---
async def run_async_orders(enctoken, orders):
    async with aiohttp.ClientSession() as session:
        tasks = [
            place_order_async(session, enctoken, order)
            for order in orders
        ]
        await asyncio.gather(*tasks)

# --- Sample Orders ---
orders = [
    {
        "variety": "regular",
        "exchange": "NSE",
        "tradingsymbol": "LIQUIDBEES",
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "quantity": 1,
        "price": 950,
        "product": "MIS",
        "validity": "DAY",
        "user_id": "DXU151"
    },
    {
        "variety": "regular",
        "exchange": "NSE",
        "tradingsymbol": "LIQUIDBEES",
        "transaction_type": "SELL",
        "order_type": "LIMIT",
        "quantity": 1,
        "price": 1050,
        "product": "MIS",
        "validity": "DAY",
        "user_id": "DXU151"
    }
]

# --- Run All ---
if __name__ == "__main__":
    enctoken = kite_login(KITE_USERNAME, KITE_PASSWORD, TOTP_KEY)
    asyncio.run(run_async_orders(enctoken, orders))
