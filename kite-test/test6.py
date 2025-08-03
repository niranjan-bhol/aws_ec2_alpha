import requests
import time

api_key = "apikey"
access_token = "accesstoken"

url = "https://api.kite.trade/orders/regular"

headers = {
    "X-Kite-Version": "3",
    "Authorization": f"token {api_key}:{access_token}"
}

data = {
    "tradingsymbol": "LIQUIDBEES",
    "exchange": "NSE",
    "transaction_type": "BUY",
    "order_type": "LIMIT",
    "price": 950,
    "quantity": 1,
    "product": "MIS",
    "validity": "DAY"
}

n = 10

start_time = time.time()

for i in range(10):
    response = requests.post(url, headers=headers, data=data)

end_time = time.time()

total_time = end_time - start_time
print(f"Total time for {n} requests: {total_time:.6f} seconds")
