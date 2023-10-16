import httpx
import pandas as pd




def fetch_zeta_orderbook_snap(symbol:str):
    data = httpx.get("https://dex-mainnet-webserver-ecs.zeta.markets/orderbooks?marketIndexes[]=137").json()
    if 'orderbooks' in data and symbol in data['orderbooks']:
        # Extract asks and bids
        asks = data['orderbooks'][symbol][0]['asks']
        bids = data['orderbooks'][symbol][0]['bids']
        
        # Convert to DataFrames
        asks_df = pd.DataFrame(asks).rename(columns={"price": "ask_price", "size": "ask_size"})
        bids_df = pd.DataFrame(bids).rename(columns={"price": "bid_price", "size": "bid_size"})
        
        # Determine max length and extend DataFrames if necessary
        max_len = max(len(bids_df), len(asks_df))
        
        bids_df = bids_df.reindex(range(max_len))
        asks_df = asks_df.reindex(range(max_len))

        # Reset index for clean merge
        bids_df = bids_df.reset_index(drop=True)
        asks_df = asks_df.reset_index(drop=True)

        # Merge DataFrames based on index
        orderbook_df = pd.concat([bids_df, asks_df], axis=1)
        orderbook_df['protocol_name'] = 'Zeta Markets'
        return orderbook_df
    else:
        print("Symbol not found in data.")
        return None

def fetch_hyperliquid_ob_snap(symbol:str):
    body = {
        "type":"l2Book",
        "coin":symbol
    }
    data = httpx.post("https://api.hyperliquid.xyz/info",json= body).json()
    
    bids_data = data['levels'][0]
    asks_data = data['levels'][1]
    
    # Convert to DataFrames
    bids_df = pd.DataFrame(bids_data)[['px', 'sz']]
    asks_df = pd.DataFrame(asks_data)[['px', 'sz']]
    
    # Rename columns and change data types
    bids_df.columns = ['bid_price', 'bid_size']
    asks_df.columns = ['ask_price', 'ask_size']

    bids_df['bid_price'] = bids_df['bid_price'].astype(float)
    bids_df['bid_size'] = bids_df['bid_size'].astype(float)

    asks_df['ask_price'] = asks_df['ask_price'].astype(float)
    asks_df['ask_size'] = asks_df['ask_size'].astype(float)
    
    # Determine max length and extend DataFrames if necessary
    max_len = max(len(bids_df), len(asks_df))
    
    bids_df = bids_df.reindex(range(max_len))
    asks_df = asks_df.reindex(range(max_len))

    # Reset index for clean merge
    bids_df = bids_df.reset_index(drop=True)
    asks_df = asks_df.reset_index(drop=True)

    # Merge DataFrames based on index
    orderbook_df = pd.concat([bids_df, asks_df], axis=1)
    orderbook_df['protocol_name'] = "Hyperliquid"
    orderbook_df.set_index("protocol_name")
    
    return orderbook_df


def fetch_vertex_ob_snap(symbol:str):
    data = httpx.get(f"https://prod.vertexprotocol-backend.com/api/v2/orderbook?ticker_id={symbol}-PERP_USDC&depth=25").json()
       # Extract bids and asks data
    bids_data = data['bids']
    asks_data = data['asks']
    
    # Convert to DataFrames
    bids_df = pd.DataFrame(bids_data, columns=['bid_price', 'bid_size'])
    asks_df = pd.DataFrame(asks_data, columns=['ask_price', 'ask_size'])

    # Determine max length and extend DataFrames if necessary
    max_len = max(len(bids_df), len(asks_df))
    
    bids_df = bids_df.reindex(range(max_len))
    asks_df = asks_df.reindex(range(max_len))

    # Reset index for clean merge
    bids_df = bids_df.reset_index(drop=True)
    asks_df = asks_df.reset_index(drop=True)

    # Merge DataFrames based on index
    orderbook_df = pd.concat([bids_df, asks_df], axis=1)
    orderbook_df['protocol_name'] = "Vertex"

    return orderbook_df


def aggregate_orderbooks(symbol: str) -> pd.DataFrame:
    zeta_df = fetch_zeta_orderbook_snap(symbol)
    hyperliquid_df = fetch_hyperliquid_ob_snap(symbol)
    vertex_df = fetch_vertex_ob_snap(symbol)

    # Combine all dataframes
    combined_df = pd.concat([zeta_df, hyperliquid_df, vertex_df])

    # Function to determine the protocol with the maximum size for each price level
    def get_max_protocol(sizes, protocols):
        max_index = sizes.idxmax()
        return protocols[max_index]

    # Group by price and aggregate sizes. We also determine the source of the max bid and ask for each price level.
    aggregated_df = combined_df.groupby('bid_price').agg(
        total_bid_size=('bid_size', 'sum'),
        bid_protocol=('protocol_name', lambda x: get_max_protocol(combined_df.loc[x.index, 'bid_size'], x))
    ).reset_index()

    aggregated_asks = combined_df.groupby('ask_price').agg(
        total_ask_size=('ask_size', 'sum'),
        ask_protocol=('protocol_name', lambda x: get_max_protocol(combined_df.loc[x.index, 'ask_size'], x))
    ).reset_index()

    # Merge bids and asks
    result_df = pd.merge(aggregated_df, aggregated_asks, how='outer', left_on='bid_price', right_on='ask_price').drop(columns=['ask_price']).rename(columns={'bid_price': 'price'}).sort_values(by='price', ascending=False)

    return result_df








    

