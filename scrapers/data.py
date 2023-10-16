import asyncio
import httpx
import pandas as pd
import time
from datetime import datetime

def fetch_curr_tvl():
    protocols = ['gmx',"vertex-protocol","Hyperliquid","zeta","drift"]
    tvl_data = []
    for protocol in protocols:
        base_url = f"https://api.llama.fi/tvl/{protocol}"
        response =httpx.get(base_url)
        if response.status_code == 200:
            tvl = int(round(response.json()))
            tvl_data.append({'Protocol': protocol, 'TVL': tvl})
    return pd.DataFrame(tvl_data)
  
def fetch_24h_vol():
    protocols = ['gmx',"vertex-protocol","hyperliquid","drift"]
    vol_data = []
    zeta_req = int(round(httpx.get('https://api.zeta.markets/global/stats').json()['volume_24h']))
    vol_data.append({'Protocol':"Zeta", "24 Hour Volume":zeta_req})
    for protocol in protocols:
        base_url = f'https://api.llama.fi/summary/derivatives/{protocol}'
        response = httpx.get(base_url)
        deriv_volume = int(round(response.json()['total24h']))
        vol_data.append({'Protocol':protocol.capitalize(), "24 Hour Volume":deriv_volume})
    return pd.DataFrame(vol_data)



def fetch_news():
    get_noa_data = httpx.get("https://news.treeofalpha.com/api/news?limit=10").json()
    df = pd.DataFrame(get_noa_data)
    # Convert the timestamp to a formatted date
    df['time'] = df['time'].apply(lambda x: datetime.utcfromtimestamp(x/1000).strftime('%d-%m-%Y %H:%M:%S'))
    # Extract the desired 'source' before the colon in the 'title' column
    df['source'] = df['title'].str.extract(r'^(.*?):')
    df['coins'] = df['suggestions'].apply(lambda x: ', '.join([item['coin'] for item in x]) if isinstance(x, list) and x else None)
    # Remove the 'source' from the 'title' column
    df['title'] = df['title'].str.replace(r'^(.*?):', '').str.strip()
    df_display = df[['source', 'title', 'coins', 'time']]
    df_display.set_index('source', inplace=True)
    return df_display
        
def fetch_dau_evm(protocol):
    dt = datetime.now().strftime("%Y-%m-%d")
    req = httpx.get(f"https://api.artemisxyz.com/asset/{protocol}/metric/UNIQUE_TRADERS/?startDate=2023-01-01&endDate={dt}").json()['data']
    df = pd.DataFrame(req, columns=['date', 'val'])
    df = df.rename(columns={'date': 'timestamp', 'val': 'dau'})
    df = df[df['dau'].notnull()]
    df['protocol_name'] = protocol
    return df

async def fetch_dau_sol(include_spot=False,name=None):
    map_programs = {
        
        "Zeta":"ZETAxsqBRek56DhiGXrn75yj2NHU3aYUnxvHXpkf3aD",
        "Drift":"dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
        "Mango-Markets-V4":"4MangoMjqJ2firMokCjjGgoK8d4MXcrgL7XJaL3w6fVg",
        
    }

    if include_spot :
        map_programs.update({  
        "Openbook": "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX",
        "Phoenix": "PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY"
        })
    headers = {'Content-Type': 'application/json'}
    results = []

    async def fetch_for_program(program_name, program_id):
        payload_template = {
            "id": "92dcff5c06f2e49",
            "type": "timeseries",
            "series": [
                {
                    "id": "GlRXvKaq33lyAKJ-UfAVM",
                    "interval": 86400000,
                    "metric": "dau",
                    "dataset": "programs:" + program_id,
                    "start": 1685304165000,
                    "end": int(time.time() * 1000)
                }
            ]
         
        }
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.vybenetwork.com/v1/query", headers=headers, json=payload_template)
            response.raise_for_status() 
           # Ensure the request was successful
            data = response.json()['series'][0]['data']
            df = pd.DataFrame(data, columns=["timestamp", "dau"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
            df["timestamp"] = df["timestamp"].dt.date
            df["protocol_name"] = program_name
            results.append(df)

            return df
    if name is None:
        tasks = [fetch_for_program(program_name, program_id) for program_name, program_id in map_programs.items()]
    else:
        if name in map_programs:
            tasks = [fetch_for_program(name, map_programs[name])]
        

    # Use asyncio.gather to run all tasks concurrently
    await asyncio.gather(*tasks)

    # Convert the results list of dataframes into one combined dataframe
    final_df = pd.concat(results)
    return final_df



def fetch_zeta_7d_volume():
    req = httpx.get("https://metabase.zeta.markets/api/public/dashboard/c0a64370-a20a-4278-b12a-2be66e4da35d/dashcard/12/card/10?parameters=%5B%7B%22type%22%3A%22date%2Frelative%22%2C%22value%22%3A%22thisweek%22%2C%22id%22%3A%22b96f7794%22%2C%22target%22%3A%5B%22dimension%22%2C%5B%22template-tag%22%2C%22epoch%22%5D%5D%7D%5D").json()['data']['rows']
    df = pd.DataFrame(req, columns=["Token", "Value"]).set_index("Token").T
    melted_df = df.melt(value_vars=df.columns, var_name='Token', value_name='Value')
    
    return melted_df

    
def fetch_zeta_coin_oi():
    req = httpx.get("https://dex-mainnet-webserver-ecs.zeta.markets/totalOpenInterest").json()['totalOpenInterest']
    tokens = list(req.keys())
    values = list(req.values())

    df = pd.DataFrame({
        'Token': tokens,
        'Value': values
    })

    return df

def fetch_historic_tvl(protocol):
    req = httpx.get(f'https://api.llama.fi/protocol/{protocol}').json()['tvl']
    df = pd.DataFrame(req)
     # Convert the timestamp to a readable format
    df["date"] = pd.to_datetime(df["date"], unit="s")
    df['protocol_name'] = protocol
    df = df.rename(columns={"totalLiquidityUSD": "TVL"})
    return df

def fetch_vol_hist(protocol):
    req= httpx.get(f"https://api.llama.fi/summary/derivatives/{protocol}").json()["totalDataChart"]
    df = pd.DataFrame(req, columns=["timestamp", "volume"])

    # Convert the timestamp to a readable format
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df['protocol_name'] = protocol
    
    return df