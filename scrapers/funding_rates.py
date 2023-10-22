import asyncio
import time
import httpx
import pandas as pd
import streamlit as st

curr_ts = int(time.time())
hl_url ="https://api.hyperliquid.xyz/info"
hl_headers = {"Content-Type": "application/json"}

def get_drift_funding():
    markets = {
        "SOL-PERP":0,
        "BTC-PERP":1,
        "ETH-PERP":2,
        "APT-PERP":3,
        "MATIC-PERP":5,
        "ARB-PERP":6,
        "DOGE-PERP":7,
        "BNB-PERP":8,
        "SUI-PERP":9,
        "1MPEPE-PERP":10
    }
    start = curr_ts-60*60*24*7
    end = curr_ts
    for market_name, index in markets.items:
        base_url = f'https://mainnet-beta.api.drift.trade/fundingRates?marketIndex={index}&from={start}&to={end}'
        req = httpx.get(base_url)
    pass
   
    
def get_hl_funding():
   
    data = {"type": "metaAndAssetCtxs"}
    req = httpx.post(url= hl_url, headers=hl_headers, json=data).json()
    # Extract 'ame values dynamically from the first item of the list in the response
    token_names = [item['name'] for item in req[0]['universe']]
    # Extract funding rates for each token in name
    new_dict = {
        'Token Name': token_names,
        'Funding Rate': [float(item['funding']) * 100 for item in req[1]],
        'Open Interest (in token)': [float(item['openInterest']) for item in req[1]]
    }
    rates_df = pd.DataFrame(new_dict).astype({"Token Name": "string", "Funding Rate": "float64", "Open Interest (in token)": "float64"})
    
    rates_df['Protocol'] = 'Hyperliquid'
    
    return rates_df

def fetch_hl_historic_funding(option):

    hist_data = {
        "type":"fundingHistory",
        "coin":option,
        "startTime":1684512000000
        }
    get_hist_rate = httpx.post(url=hl_url,headers=hl_headers,json= hist_data).json()

    df = pd.DataFrame(get_hist_rate)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df['time'] = df['time'].dt.floor('s')

    # Set 'time' as the index
    df.set_index('time', inplace=True)
    df =df.drop('coin',axis=1)
    return df

def fetch_vertex_funding(symbol = None):
    product_id_to_symbol = {
        2: "BTC",
        4: "ETH",
        6: "ARB",
        8:"BNB",
        10:"XRP",
        12:"SOL",
        14:"MATIC",
        16:"SUI",
        18:"OP",
        20:"APT",
        22:"LTC",
        24:"BCH",
        26:"COMP",
        28:"MKR",
        30:"PEPE",
        34:"DOGE",
        36:"LINK",
        38:"DYDX",
        40:"CRV"
    }

    json_data = {
            
            "funding_rates": {
                "product_ids": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 34, 36, 38, 40]
            
            }
        }

    data = httpx.post("https://prod.vertexprotocol-backend.com/indexer",json=json_data).json()

    converted_data = []

    for key, value in data.items():
        product_id = value['product_id']
        symbol = product_id_to_symbol.get(product_id)
        
        if symbol:  # Only process if the symbol exists in the map
            funding_rate = (int(value['funding_rate_x18']) / 10**18) / 24
            converted_data.append({
                'Token Name': symbol,
                'Funding Rate': funding_rate,
            })

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(converted_data)
    df['Protocol'] = 'Vertex'
    return df

def fetch_mango_funding():
    data = httpx.get("https://api.mngo.cloud/data/v4/stats/perp-market-summary").json()
    extracted_rates = []
    for symbol, data_list in data.items():
        if data_list:  # Check if the list is not empty
            data_dict = data_list[0]  # Assuming there's only one dictionary per list
            funding_rate = data_dict.get("funding_rate")
            clean_symbol = symbol.replace("-PERP", "")  # Removing the -PERP suffix
            extracted_rates.append({
                'Token Name': clean_symbol,
                'Funding Rate': funding_rate
            })

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(extracted_rates)
    df['Protocol'] = 'Mango'
    return(df)