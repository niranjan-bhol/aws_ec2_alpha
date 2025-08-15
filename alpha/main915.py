import aiohttp
import asyncio
from datetime import datetime

api_key = "8n5mz9cmhf4dpaci"
access_token = "80EPoDEv3W9Ckcex5uo6G6MnlusA2YlQ"

url = "https://api.kite.trade/orders/regular"

headers = {
    "X-Kite-Version": "3",
    "Authorization": f"token {api_key}:{access_token}"
}

payloads = [
    {
        "tradingsymbol": "LIQUIDBEES",
        "exchange": "NSE",
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "price": 950,
        "quantity": 1,
        "product": "MIS",
        "validity": "DAY"
    },
    {
        "tradingsymbol": "LIQUIDBEES",
        "exchange": "NSE",
        "transaction_type": "SELL",
        "order_type": "LIMIT",
        "price": 1050,
        "quantity": 1,
        "product": "MIS",
        "validity": "DAY"
    }
]

def wait_until_exact(hour, minute, second, microsecond):
    target = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
    if target <= datetime.now():
        return
    while True:
        now = datetime.now()
        if now >= target:
            break

async def post_order(session, payload):
    async with session.post(url, headers=headers, data=payload) as resp:
        await resp.json()

async def main():
    print(f"{datetime.now()} | Program Started")
    wait_until_exact(9, 15, 0, 0)
    async with aiohttp.ClientSession() as session:
        tasks = [post_order(session, payload) for payload in payloads]
        await asyncio.gather(*tasks)
    print(f"{datetime.now()} | All orders executed")

if __name__ == "__main__":
    asyncio.run(main())
