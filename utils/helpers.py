import httpx
import pandas as pd


def color_green(val):
    return 'color: green'
def color_red(val):
    return 'color: red'

def fetch_aevo_assets():
    symbols = httpx.get("https://api.aevo.xyz/assets").json()
    return symbols



def process_data_from_url(url):
    # Load the data from the URL
    df = pd.read_csv(url, parse_dates=["timestamp"])
    protocol_name = df['protocol_name'].iloc[0]
    # Calculate the spread
    grouped = df.groupby('timestamp')
    top_bid = grouped['bid_price'].max()
    low_ask = grouped['ask_price'].min()
    spread = low_ask - top_bid

    # Calculate the mid price
    mid_price = (top_bid + low_ask) / 2

    # Calculate the spread percentage
    spread_percentage = (spread / mid_price) * 100

    # Return as a DataFrame
    return pd.DataFrame({
        'timestamp': spread_percentage.index,
        'spread_percentage': spread_percentage.values,
        'protocol_name': protocol_name
    })
