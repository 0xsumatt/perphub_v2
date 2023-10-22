import httpx
import time
curr_ts = time.time()

import pandas as pd
import httpx
import time

curr_ts = time.time()

def get_drift_funding():
    import pandas as pd
    from_ts = int(curr_ts-60)
    to_ts = int(curr_ts)
    print(from_ts)
    print(to_ts)

    # Mapping dictionary with market indices as keys
    markets = {
        0: "SOL-PERP",
        1: "BTC-PERP",
        2: "ETH-PERP",
        3: "APT-PERP",
        5: "MATIC-PERP",
        6: "ARB-PERP",
        7: "DOGE-PERP",
        8: "BNB-PERP",
        9: "SUI-PERP",
        10: "1MPEPE-PERP"
    }

    # Fetch data from the HTTP endpoint and process the response
    extracted_data = []
    for market_index, market_symbol in markets.items():
        response = httpx.get(f"https://mainnet-beta.api.drift.trade/fundingRates?marketIndex={market_index}&from={from_ts}&to={to_ts}")
        if response.status_code == 200:
            market_data = response.json()['fundingRates']  # Assuming the response is in JSON format
            for entry in market_data:
                extracted_data.append({
                    'fundingRate': entry['fundingRate'],
                    'marketIndex': entry['marketIndex'],
                    'markPriceTwap': entry['markPriceTwap'],
                    'symbol': market_symbol,
                    'slot':entry['slot']
                })

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(extracted_data)

    print(df)


get_drift_funding()