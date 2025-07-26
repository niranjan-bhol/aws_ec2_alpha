import requests

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

response = requests.post(url, headers=headers, data=data)

print("Status code:", response.status_code)
print("Response:", response.json())
