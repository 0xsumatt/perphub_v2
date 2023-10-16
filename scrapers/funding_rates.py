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
    client = httpx.Client()
    data = {"type": "metaAndAssetCtxs"}
    req = client.post(url= hl_url, headers=hl_headers, json=data).json()
    # Extract 'ame values dynamically from the first item of the list in the response
    token_names = [item['name'] for item in req[0]['universe']]
    # Extract funding rates for each token in name
    new_dict = {
        'Token Name': token_names,
        'Funding Rate': [float(item['funding']) * 100 for item in req[1]],
        'Open Interest (in token)': [float(item['openInterest']) for item in req[1]]
    }
    rates_df = pd.DataFrame(new_dict).astype({"Token Name": "string", "Funding Rate": "float64", "Open Interest (in token)": "float64"})
    
    # Set index to 'Token Name' and transpose the DataFrame
    rates_df = rates_df.set_index('Token Name').T
    
    client.close()
    return rates_df

def fetch_historic_funding():
    client = httpx.Client()
    data = {"type":"meta"}
    
    init_req = client.post(url=hl_url,headers=hl_headers,json=data).json()
    token_names = [item['name'] for item in init_req['universe']]
    option = st.selectbox("Select a Coin",token_names)


    hist_data = {
        "type":"fundingHistory",
        "coin":option,
        "startTime":1684512000000
        }
    get_hist_rate = client.post(url=hl_url,headers=hl_headers,json= hist_data).json()

    df = pd.DataFrame(get_hist_rate)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df['time'] = df['time'].dt.floor('s')

    # Set 'time' as the index
    df.set_index('time', inplace=True)
    df =df.drop('coin',axis=1)
    client.close()
    return df