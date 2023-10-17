import httpx
import time
import streamlit as st
import json

from driftpy.clearing_house import ClearingHouse 
from driftpy.constants.numeric_constants import BASE_PRECISION, AMM_RESERVE_PRECISION 

from anchorpy import Provider
from anchorpy import Wallet
from solana.keypair import Keypair
from driftpy.constants.config import configs
from solana.rpc.async_api import AsyncClient
from driftpy.clearing_house_user import ClearingHouseUser
from driftpy.math.positions import is_available
from solana.publickey import PublicKey
import pandas as pd
from anchorpy import Program
from driftpy.accounts import get_user_account_public_key


hl_url ="https://api.hyperliquid.xyz/info"
hl_headers = {"Content-Type": "application/json"}
def zeta_trade_history(address:str,market = None):
    if market is not None:
        url = f'https://api.zeta.markets/account/{address}/trades?market={market}'
    else:
        url = f'https://api.zeta.markets/account/{address}/trades'
    trades = httpx.get(url).json()['trades']
    extracted_data = [{'blockTime': trade['blockTime'], 'price': trade['price'],'asset':trade['asset'], 'isBid': trade['isBid']} for trade in trades]
    df = pd.DataFrame(extracted_data)
    return df

def get_bybit_data(symbol:str,interval = None):
    if len(symbol) != 0:
        current_time = (time.time())
        if interval is not None:
            url = f'https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}USDT&interval={interval}&start={current_time-(60 * 60 * 24 * 365)}&end={current_time}'
        else:
            url = f'https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}USDT&interval=240&start={current_time-(60 * 60 * 24 * 365)}&end={current_time}&limit=1000'
        
        get_klines = httpx.get(url)
        st.write(get_klines)
        get_klines = json.loads(get_klines)['result']['list']
        timestamps = [entry[0] for entry in get_klines]
        closing_prices = [entry[4] for entry in get_klines]
        opening_prices = [entry[1] for entry in get_klines]
        # Creating a DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'opening_price':opening_prices,
            'closing_price': closing_prices
        })
        return df


def fetch_hl_positions(lookup):
    
        client = httpx.Client()
        data = {
            "type": "clearinghouseState",
            "user": lookup
        }

        req = client.post(url=hl_url, headers=hl_headers, json=data).json()['assetPositions']
        positions_list = []

        for position in req:
          
                entry_px = position["position"]["entryPx"]

                if entry_px and entry_px != '0.0':
                    coin = position["position"]["coin"]
                    liquidation_px = position["position"]["liquidationPx"]
                    position_value = position["position"]["positionValue"]
                    unrealized_pnl = position["position"]["unrealizedPnl"]

                    position_dict = {
                        "Coin": coin,
                        "Entry Price": float(entry_px),
                        "liquidation Price": float(liquidation_px) if liquidation_px and liquidation_px != '0.0' else None,
                        "Position Value": float(position_value) if position_value and position_value != '0.0' else None,
                        "Unrealized Pnl": float(unrealized_pnl) if unrealized_pnl and unrealized_pnl != '0.0' else None
                    }
                    positions_list.append(position_dict)

            
        try:
            df = pd.DataFrame(positions_list).astype({
                "Coin": "string",
                "Entry Price": "float64",
                "liquidation Price": "float64",
                "Position Value": "float64",
                "Unrealized Pnl": "float64",
            })
            client.close()
            return df
        except Exception:
                st.header("No Positions Found")

def fetch_open_hl_orders(lookup):
    if len(lookup) != 0:
        data = {
            "type": "openOrders",
            "user": lookup
        }
        req = httpx.post(url=hl_url, headers=hl_headers, json=data).json()
        if not req:
            st.header("no open orders")
        else:
            df = pd.DataFrame(req)
            df["timestamp"] = pd.to_datetime(df["timestamp"] / 1000, unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
            df_dtype = df.astype({
                "timestamp": "string",
                "coin": "string",
                "limitPx": "float64",
                "oid": "Int64",
                "side": "string",
                "sz": "float64",
            })
            return df_dtype
   
   
def fetch_hl_fills(lookup):
    if len(lookup)!= 0:
        data = {
            "type":"userFills",
            "user":lookup
        }
        data = httpx.post(url=hl_url,headers =hl_headers,json =data).json()
        trade_data = [{'symbol':trade['coin'],'price': trade['px'], 'timestamp': trade['time'], 'side': trade['side']} for trade in data]
        # Convert to DataFrame
        df = pd.DataFrame(trade_data)

        return df

async def drift_pos_lookup(authority,subaccount=None):
    authority = PublicKey(authority)
    env = 'mainnet'
    config = configs[env]
    wallet = Wallet(Keypair())
    connection = AsyncClient(config.default_http)
    provider = Provider(connection,wallet)
    ch = ClearingHouse.from_config(config,provider)
    chu = ClearingHouseUser(ch,authority=authority)
    user = await chu.get_user()
    market_index_mapping = {
        0: 'SOL-PERP'
        
    }

    data_list = []
    for position in user.perp_positions:
        if not is_available(position):

            adjusted_base_asset_amount = position.base_asset_amount / 10**9
            adjusted_settled_pnl = position.settled_pnl / 10**6
            # Map the market index
            market_name = market_index_mapping.get(position.market_index, position.market_index)
            data_dict = {
                'base_asset_amount': adjusted_base_asset_amount,
                'market_index': market_name,
                'settled_pnl': adjusted_settled_pnl
            }
            data_list.append(data_dict)
    df = pd.DataFrame(data_list).set_index("market_index")

    return df  

async def fetch_drift_trades(authority,month):
  
    authority = PublicKey(authority)
    env = 'mainnet'
    config = configs[env]
    wallet = Wallet(Keypair())
    connection = AsyncClient(config.default_http)
    provider = Provider(connection,wallet)
    clearing_house :ClearingHouse= ClearingHouse.from_config(config,provider)
    user_account_pubk = get_user_account_public_key(clearing_house.program_id,
                    authority,
                    0)
    url = f"https://drift-historical-data.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/user/{user_account_pubk}/trades/2023/{month}"
    data = pd.read_csv(url,nrows=5000)
    df=pd.DataFrame(data)
    address =str(user_account_pubk)
    filtered_new_df = df[(df['taker'] == address) | (df['maker'] == address)].copy()
    # Determine the direction of the trade
    trade_directions_new = filtered_new_df.apply(
        lambda row: row['takerOrderDirection'] if row['taker'] == address else row['makerOrderDirection'],
        axis=1
    )
    mapped_trade_directions_new = trade_directions_new.map({"long": "B", "short": "A"})
    # Assign the trade directions to the dataframe
    filtered_new_df['trade_direction'] = mapped_trade_directions_new
    # Extract relevant columns
    final_new_df = filtered_new_df[['ts', 'oraclePrice', 'trade_direction']]
    final_new_df = final_new_df.rename(columns={
    'ts': 'timestamp',
    'oraclePrice': 'price',
    'trade_direction': 'side'
        })

    return final_new_df

def fetch_zeta_trades(pubkey):
     data = httpx.get(f"https://api.zeta.markets/account/{pubkey}/trades").json()['trades']
     trade_data = [{"symbol":trade['asset'],"price":trade['price'],"timestamp":trade['blockTime'],"side":trade['isBid']} for trade in data]
     df = pd.DataFrame(trade_data)
     df['side'] = df['side'].map({True: "B", False: "A"})
     return df


     
