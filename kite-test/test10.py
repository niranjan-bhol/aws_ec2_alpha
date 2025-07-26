import aiohttp
import asyncio
import time

api_key = "apikey"
access_token = "accesstoken"

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
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "price": 950,
        "quantity": 1,
        "product": "MIS",
        "validity": "DAY"
    }
]

async def post_order(session, payload):
    async with session.post(url, headers=headers, data=payload) as resp:
        await resp.json()

async def main():
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [post_order(session, payload) for payload in payloads]
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time for {len(payloads)} requests: {total_time:.6f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
