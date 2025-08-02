import numpy as np
import pandas as pd
import requests
from yahooquery import Ticker
from tabulate import tabulate
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

# --- API Credentials ---
api_key = "8n5mz9cmhf4dpaci"
access_token = "ajdvU55kqb1eF9dODt9U78QGgnQjyvB5"

"""
# --- Read Access Token from access_token.txt ---
with open("access_token.txt", "r") as file:
    access_token = file.read().strip()
"""

# --- ETF-Underlying Mapping ---
etf_mapping = {
    "NIFTYBEES": {
        "etf": {"zerodha": "NIFTYBEES", "yahoo": "NIFTYBEES.NS"},
        "underlying": {"name": "NIFTY 50", "zerodha": "NIFTY 50", "yahoo": "^NSEI"}
    },
    "BANKBEES": {
        "etf": {"zerodha": "BANKBEES", "yahoo": "BANKBEES.NS"},
        "underlying": {"name": "NIFTY BANK", "zerodha": "NIFTY BANK", "yahoo": "^NSEBANK"}
    },
    "ITBEES": {
        "etf": {"zerodha": "ITBEES", "yahoo": "ITBEES.NS"},
        "underlying": {"name": "NIFTY IT", "zerodha": "NIFTY IT", "yahoo": "^CNXIT"}
    }
}

# --- Fetch Equity Margin ---
def get_equity_margin(api_key, access_token):
    url = "https://api.kite.trade/user/margins"
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()["data"]["equity"]["net"]

# --- Fetch ETF Volume (Last N Days) ---
def fetch_etf_volume(etf_mapping, days=90):
    yahoo_symbols = [v["etf"]["yahoo"] for v in etf_mapping.values()]
    end = datetime.today()
    start = end - timedelta(days=days)
    t = Ticker(yahoo_symbols)
    hist = t.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval="1d").reset_index()
    df = hist.pivot(index="date", columns="symbol", values="volume").dropna()
    return df

# --- Volume Calculations ---
def calculate_average_volume(df):
    return df.mean().round().astype(int)

def calculate_safe_volume(avg_volume_series, divisor=5000):
    return (avg_volume_series / divisor).round().astype(int)

# --- Fetch Historical Closing Prices ---
def fetch_price_data(etf_mapping, start="2021-01-01", end=None):
    if end is None:
        end = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    symbols = []
    for pair in etf_mapping.values():
        symbols.append(pair["etf"]["yahoo"])
        symbols.append(pair["underlying"]["yahoo"])
    t = Ticker(symbols)
    hist = t.history(start=start, end=end, interval="1d").reset_index()
    df = hist.pivot(index="date", columns="symbol", values="close").dropna()
    return t, df

# --- Predict ETF Opening Price from Index Opening ---
def predict_etf_price(t, df, index_sym, etf_sym):
    X = df[index_sym].values.reshape(-1, 1)
    y = df[etf_sym].values
    model = LinearRegression().fit(X, y)
    index_open = t.quotes[index_sym]["regularMarketOpen"]
    predicted_price = model.predict(np.array([[index_open]]))[0]
    return predicted_price

# --- Adjust Volumes Based on Margin and Prediction ---
def calculate_adjusted_volume(discount_margin, predicted, safe_volume):
    total_safe_value = sum(
        predicted[etf] * safe_volume.loc[etf]
        for etf in safe_volume.index
        if etf in predicted
    )
    allocation_ratio = discount_margin / total_safe_value if total_safe_value > 0 else 0
    adjusted_volumes = {
        etf: int(allocation_ratio * safe_volume.loc[etf])
        for etf in safe_volume.index
        if etf in predicted
    }
    return adjusted_volumes

# --- Generate & Print Processed Data Table ---
def display_processed_data_table(etf_mapping, avg_volumes, safe_volumes, adjusted_volumes, t, price_df, predicted_prices):
    table = []
    sn = 1
    
    for etf_key, data in etf_mapping.items():
        etf_zerodha = data["etf"]["zerodha"]
        underlying_zerodha = data["underlying"]["zerodha"]
        etf_yahoo = data["etf"]["yahoo"]
        index_yahoo = data["underlying"]["yahoo"]
        
        avg_vol = int(avg_volumes.get(etf_yahoo, 0))
        safe_vol = int(safe_volumes.get(etf_yahoo, 0))
        adjusted_vol = int(adjusted_volumes.get(etf_yahoo, 0))
        
        underlying_open = t.quotes[index_yahoo]["regularMarketOpen"]
        
        predicted = predicted_prices.get(etf_yahoo, "N/A")
        if isinstance(predicted, float):
            predicted = f"{predicted:.2f}"
        
        row = [
            sn,
            etf_zerodha,
            underlying_zerodha,
            avg_vol,
            safe_vol,
            adjusted_vol,
            underlying_open,
            predicted
        ]
        table.append(row)
        sn += 1
    
    headers=["SN", "ETF", "Underlying Asset", "Avg Volume", "Safe Volume", "Adjusted Volume", "Underlying Asset Open Price", "Predicted Price"]
    table = tabulate(table, headers, tablefmt="psql")
    print("\nProcessed Data Table:")
    print(table)

# --- Generate Orders Table ---
def generate_order_data(adjusted_volumes, predicted_prices, etf_mapping):
    data = []
    for i, etf_yahoo in enumerate(adjusted_volumes.keys(), 1):
        qty = adjusted_volumes[etf_yahoo]
        pred = predicted_prices.get(etf_yahoo, 0)
        buy_price = round(pred * 0.995, 2)
        sell_price = round(pred * 1.005, 2)
        
        zerodha_etf = next((v["etf"]["zerodha"] for v in etf_mapping.values() if v["etf"]["yahoo"] == etf_yahoo), etf_yahoo)
        
        data.append([i, zerodha_etf, qty, buy_price, sell_price])
    return data

# --- Print Orders Table ---
def print_order_table(order_data):
    headers = ["SN", "ETF", "Quantity", "Buy Price", "Sell Price"]
    table = tabulate(order_data, headers=headers, tablefmt="psql")
    print("\nOrder Table:")
    print(table)

# --- Generate & Store Payloads ---
def write_payloads_to_file(order_data, filename="payload.txt", pyfile="payload.py",):
    payloads = []
    
    for row in order_data:
        _, tradingsymbol, quantity, buy_price, sell_price = row
        
        # Ensure prices are regular float (not np.float64)
        buy_price = float(buy_price)
        sell_price = float(sell_price)
        
        # BUY order
        payloads.append({
            "tradingsymbol": tradingsymbol,
            "exchange": "NSE",
            "transaction_type": "BUY",
            "order_type": "LIMIT",
            "price": buy_price,
            "quantity": quantity,
            "product": "MIS",
            "validity": "TTL",
            "validity_ttl": "1"
        })
        
        # SELL order
        payloads.append({
            "tradingsymbol": tradingsymbol,
            "exchange": "NSE",
            "transaction_type": "SELL",
            "order_type": "LIMIT",
            "price": sell_price,
            "quantity": quantity,
            "product": "MIS",
            "validity": "TTL",
            "validity_ttl": "1"
        })
    
    # Write to file as valid Python dict list
    with open(filename, "w") as f:
        f.write("payloads = [\n")
        for payload in payloads:
            f.write("    " + str(payload) + ",\n")
        f.write("]")
    with open(pyfile, "w") as f:
        f.write("payloads = [\n")
        for payload in payloads:
            f.write("    " + str(payload) + ",\n")
        f.write("]")
    
    print(f"\nGenerated and Stored Payloads")

# --- Main Logic ---
if __name__ == "__main__":
    # Step 1: Get available margin
    equity_net = get_equity_margin(api_key, access_token)
    leverage_margin = equity_net * 5
    discount_margin = leverage_margin - (leverage_margin * 0.05)

    print(f"\nAvailable Margin  : ₹{equity_net:,.2f}")
    print(f"Leveraged Margin  : ₹{leverage_margin:,.2f}")
    print(f"Discounted Margin : ₹{discount_margin:,.2f}")

    # Step 2: Get average and safe volumes
    volume_df = fetch_etf_volume(etf_mapping)
    avg_volumes = calculate_average_volume(volume_df)
    safe_volumes = calculate_safe_volume(avg_volumes)

    # Step 3: Predict ETF Opening Prices
    t, price_df = fetch_price_data(etf_mapping)
    predicted_prices = {}

    for etf, data in etf_mapping.items():
        etf_yahoo = data["etf"]["yahoo"]
        index_yahoo = data["underlying"]["yahoo"]
        predicted = predict_etf_price(t, price_df, index_yahoo, etf_yahoo)
        predicted_prices[etf_yahoo] = predicted

    # Step 4: Adjust volume per ETF based on prediction & margin
    adjusted_volumes = calculate_adjusted_volume(discount_margin, predicted_prices, safe_volumes)

    # Step 5: Generate and print tables
    display_processed_data_table(etf_mapping, avg_volumes, safe_volumes, adjusted_volumes, t, price_df, predicted_prices)

    order_data = generate_order_data(adjusted_volumes, predicted_prices, etf_mapping)
    print_order_table(order_data)

    # Step 6: Export Payloads
    write_payloads_to_file(order_data)
