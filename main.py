import streamlit as st
from charts import *
from scrapers.data import *
from scrapers.funding_rates import *
from scripts.beta import beta_calculator
from scrapers.lookups import *
from scrapers.orderbooks import *
from streamlit_autorefresh import st_autorefresh
from utils.helpers import *

alt.data_transformers.disable_max_rows()
def main():

    st.set_page_config(
        layout = "wide",
        page_title='Home',
        page_icon="random"
    )
    # Extract the current tab from the URL's query parameters
    query_params = st.experimental_get_query_params()
    current_tab = query_params.get('tab', ['Home'])[0]

    # Define the available tabs
    tabs = ["Home","Funding Rates","Spread Data","Solana","Hyperliquid","Tools","Useful Links"]

    
    selected_tab = st.sidebar.radio("Navigate to:", tabs, index=tabs.index(current_tab))

    
    if selected_tab != current_tab:
        st.experimental_set_query_params(tab=selected_tab)

    colour_scheme = {
        "Drift":"#6369D1",
        "Vertex-Protocol":"#EDC79B",
        "Hyperliquid":"#99F7AB",
        "Zeta":"#F75590",
        "Mango-Markets-V4":"#FF9F1C"
    }

   
    match selected_tab:

     case "Home":
        st.write("")
        refresh = st_autorefresh(300000)
        st.markdown("News refreshes every 5 minutes using the News of Alpha feed")
        st.write(fetch_news())
   
        protocols = ['Drift','Vertex-Protocol','Hyperliquid','Zeta','Mango-Markets-V4']
        
        sol_dau_data = asyncio.run(fetch_dau_sol())
            # Fetch data for the 2nd protocol
        df_vertex = fetch_dau_evm(protocols[1].replace('-Protocol', ''))
        df_vertex['protocol_name'] = df_vertex['protocol_name'].replace('Vertex', 'Vertex-Protocol')

            # Fetch data for the 3rd protocol
        df_hyperliquid = fetch_dau_evm(protocols[2].replace('-Protocol', ''))   

        df = pd.concat([df_hyperliquid,df_vertex,sol_dau_data],ignore_index=True)
       
        chart =create_line_chart(df, 'timestamp', 'dau', title="Daily Active Users (DAU) Over Time", color='protocol_name',color_scheme=colour_scheme)
        st.altair_chart(chart,use_container_width=True)
        cutoff_date = pd.Timestamp('2023-06-16')
        vol_dfs = []
        for protocol in protocols:
            df_protocol = fetch_vol_hist(protocol)
            df_protocol = df_protocol[df_protocol['timestamp'] > cutoff_date]
            vol_dfs.append(df_protocol)
            

        
        combined_df = pd.concat(vol_dfs)

        chart = create_line_chart(combined_df, 'timestamp:T', 'volume:Q', title="Protocol Volume Over Time", color='protocol_name',color_scheme=colour_scheme)
        st.altair_chart(chart,use_container_width=True)
        tvl_dfs = []
        for protocol in protocols:
            df_protocol = fetch_historic_tvl(protocol)
            df_protocol = df_protocol[df_protocol['date'].dt.year >= 2023]
            
            tvl_dfs.append(df_protocol)

            
        combined_dfs = pd.concat(tvl_dfs)

        
        chart = create_line_chart(combined_dfs, 'date:T', 'TVL:Q', title="Total Value locked (TVL) Over Time", color='protocol_name',color_scheme=colour_scheme)

        st.altair_chart(chart,use_container_width=True)
        refresh

     case "Funding Rates":
        st.write("")
        st.markdown("Live funding rates from multiple exchanges")
        def highlight_colors(val):
            return color_green(val) if val > 0 else color_red(val)
        
        hl_df = get_hl_funding()
        #vertex_df = fetch_vertex_funding()
        mango_df = fetch_mango_funding()
        aevo_df = asyncio.run(fetch_aevo_funding())
        # Concatenate the dataframes vertically
        combined_df = pd.concat([hl_df,aevo_df,mango_df])
        
        # Reshape the combined dataframe using pivot_table
        final_df = combined_df.pivot_table(index='Token Name', columns='Protocol', values='Funding Rate', aggfunc='first')
        final_df = final_df.T
        styled_df = final_df.style.applymap(highlight_colors)
        st.write(styled_df.to_html(), unsafe_allow_html=True)
    
        st.title("Historic Funding Rates")
        st.markdown("Currently only Hyperliquid is supported")
        data = {"type":"meta"}
        init_req = httpx.post(url=hl_url,headers=hl_headers,json=data).json()
        token_names = [item['name'] for item in init_req['universe']]
        options = st.selectbox("Select a Coin",token_names)
        df = fetch_hl_historic_funding(option=options)
        df_trans = df.T
        st.write(df_trans)
    
        
     case "Spread Data":
        st.title("Charts of Spread percentages for tokens over time")
        st.markdown("""
                    [Raw data for these can be found here]("https://github.com/0xsumatt/orderbook_snaps")
                    """)
        asset = st.selectbox("Select a Token",['BTC','ETH','SOL','ARB'])
        urls = [f"https://raw.githubusercontent.com/0xsumatt/orderbook_snaps/master/hyperliquid_{asset}_orderbook_snap.csv",f"https://raw.githubusercontent.com/0xsumatt/orderbook_snaps/master/zeta_{asset}_orderbook_snap.csv",f"https://raw.githubusercontent.com/0xsumatt/orderbook_snaps/master/vertex_{asset}_orderbook_snap.csv"]  # List of your URLs
        results = []

        for url in urls:
            df = process_data_from_url(url)
            
            results.append(df)

        # Concatenate results
        final_df = pd.concat(results)
        spread_scheme = {
            "Hyperliquid":"#99F7AB",
            "Vertex":"#EDC79B",
            "Zeta Markets":"#F75590"
        }
       
        chart = create_line_chart(final_df, 'timestamp', 'spread_percentage', title="Spread Percentage over Time", color='protocol_name',color_scheme=spread_scheme)
        st.altair_chart(chart,use_container_width=True)

     case "Solana":
        st.write("")
        st.markdown("TVL data is currently provided by DefiLlama and DAU data provided by VybeNetwork")
        sub_tabs = ["All","Zeta"]
        current_sub_tab = query_params.get('sub_tab', ['All'])[0]
        selected_sub_tab = st.radio("Choose:", sub_tabs, index=sub_tabs.index(current_sub_tab))
        match selected_sub_tab:

            case "All":
                sol_colour_scheme = {
                    "Phoenix":"#ba181b",
                    "Openbook":"#dee2ff",
                    "Zeta":"#F75590",
                    "Drift":"#6369D1",
                    "Mango-Markets-V4":"#FF9F1C"
                }
                include_spot_clobs = st.checkbox('Include Pheonix and Openbook ?')
                sol_dau_data = asyncio.run(fetch_dau_sol(include_spot_clobs))
                chart = create_line_chart(sol_dau_data, x_column="timestamp", y_column="dau", color="protocol_name",color_scheme=sol_colour_scheme)
                st.altair_chart(chart,use_container_width=True)
                Sol_protocol_list=['Drift','Zeta','Mango-Markets-V4']
                vol_list = []
                for protocol in Sol_protocol_list:
                    sol_vol_data = fetch_vol_hist(protocol)
                    vol_list.append(sol_vol_data)

                comb_df = pd.concat(vol_list)
                chart = create_line_chart(comb_df, 'timestamp:T', 'volume:Q', title="Protocol Volume Over Time", color='protocol_name',color_scheme=sol_colour_scheme)
                st.altair_chart(chart,use_container_width=True)
            
            case "Zeta":
                colour_scheme = {
                    "ARB":"#3a86ff",
                    "APT":"#7cb518",
                    "SOL":"#8338ec",
                    "BTC":"#fb5607",
                    "ETH":"#e4ff1a",
                }

                st.title("Zeta Markets")
                col1,col2 = st.columns(2)
                oi_data = fetch_zeta_coin_oi()
                oi_chart = create_bar_chart(oi_data,'Token', 'Value', title="Open Interest (denominated in tokens)",color_scheme=colour_scheme)
                col1.altair_chart(oi_chart)

                week_vol_data = fetch_zeta_7d_volume()
                weekly_chart = create_bar_chart(week_vol_data,'Token', 'Value', title="7D Volume (denominated in $)",color_scheme=colour_scheme)
                col2.altair_chart(weekly_chart)

                hist_vol_data = fetch_vol_hist("zeta")
                hist_vol_chart = create_line_chart(hist_vol_data, "timestamp", 'volume', title="Volume over time")
                col1.altair_chart(hist_vol_chart, use_container_width=True)
                
                dau_data = asyncio.run(fetch_dau_sol(name = "Zeta"))
               
                dau_chart = create_line_chart(dau_data,"timestamp",'dau',title = "DAU over time")
                col2.altair_chart(dau_chart,use_container_width=True)

            case "Drift":
                st.write("Coming Soon")
       
     case "Hyperliquid":
          st.title("Hyperliquid")
          st.write("Current funding rates")
          st.write(get_hl_funding())
          c1,c2 = st.columns(2)
          vol_data = fetch_vol_hist("hyperliquid")
          vol_data_chart = create_line_chart(vol_data,'timestamp','volume',title="Volume over time")
          c1.altair_chart(vol_data_chart,use_container_width=True)
          dau_data = fetch_dau_evm("hyperliquid")
          dau_chart = create_line_chart(dau_data,"timestamp",'dau',title = "Daily Active Users Over Time")
          c2.altair_chart(dau_chart,use_container_width=True)
         
     case "Tools":
        sub_tabs = ["Beta Calculator","Position Lookups","Historic Trade Visualisations","Backtester","Orderbook Snapshots","Consolidated Orderbook Density"]
        current_sub_tab = query_params.get('sub_tab',['Beta Calculator'])[0]
        selected_sub_tab = st.radio("Choose:", sub_tabs, index=sub_tabs.index(current_sub_tab))
        match selected_sub_tab:
            case "Beta Calculator":
                st.title("Beta Calculator")
                st.markdown('This pulls data from yahoo finance so please enter the tickers exactly how they appear there')
                # Input for ticker_1 which can be single or multiple assets
                ticker_1 = st.text_input("Enter the asset(s) (comma-separated for multiple assets):").split(',')
                # Input for ticker_2 (the benchmark)
                ticker_2 = st.text_input("Enter the benchmark asset:")
                start_date = st.date_input("Start date")
                end_date = st.date_input("End date")
                # Check if all inputs are provided
                if ticker_1 and ticker_2 and start_date and end_date:

                    # Remove any whitespace from the ticker names
                    ticker_1 = [ticker.strip() for ticker in ticker_1]
                    # Create an instance of the beta_calculator
                    beta_calc = beta_calculator(ticker_1, ticker_2, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                    # Calculate the beta
                    beta = beta_calc.calc_beta()
                   
                    st.write(f"The beta of {', '.join(ticker_1)} against {ticker_2} is: {beta:.2f}")


            case "Historic Trade Visualisations":
               
                exchange = st.selectbox("Select an Exchange",['Drift',"Hyperliquid","Zeta"])
                symbol = st.selectbox("Select a symbol:", ["BTC", "ETH", "SOL", "ARB","SUI"]) 
                chart_interval = st.selectbox("Select an Interval",["Default","1m","5m","1h","2h","4h","D","W"])
                interval_map = {
                    "1m":1,
                    "5m":5,
                    "1h":60,
                    "4h":240,
                    "D":"1d",
                    "W":"1w"
                    }
                 
                address = st.text_input(label ="Enter address", placeholder="0x00")
                date = st.date_input("Select a Date(Only month is used)and for Drift Only")
                numeric_interval = interval_map.get(chart_interval)
                if len(address)>0 :
                    match exchange :
                        
                        case 'Zeta' :
                            if chart_interval == 'Default':
                                df_oracle_prcing = get_drift_klines(symbol,exchange="Zeta")
                            else:
                                df_oracle_prcing = get_drift_klines(symbol,exchange="Zeta",interval=numeric_interval)
                            df_oracle_prcing['timestamp'] = pd.to_datetime(df_oracle_prcing['timestamp'], unit='ms') 
                            df_zeta = fetch_zeta_trades(address)
                            df_zeta= df_zeta[df_zeta['symbol'] == symbol]
                            df_zeta['timestamp'] = pd.to_datetime(df_zeta['timestamp'], unit='s') 
                            chart = create_interactive_chart(df_oracle_prcing, exchange_df=df_zeta, width=1000, height=600)
                            st.altair_chart(chart)
                        case 'Drift' :
                            if chart_interval == 'Default':
                                df_fill_pricing = get_drift_klines(symbol,exchange="Drift")
                            else:
                                df_fill_pricing = get_drift_klines(symbol,exchange="Drift",interval=numeric_interval)
                            df_fill_pricing['timestamp'] = pd.to_datetime(df_fill_pricing['timestamp'], unit='ms') 
                            selected_month = date.month
                            df_drift = asyncio.run(fetch_drift_trades(address,selected_month))
                            df_drift['timestamp'] = pd.to_datetime(df_drift['timestamp'], unit='s')
                            chart = create_interactive_chart(df_fill_pricing, exchange_df=df_drift, width=1000, height=600)
                            st.altair_chart(chart)
                        case "Hyperliquid":
                            if chart_interval == 'Default':
                                df_hl_klines = get_hyperliquid_klines(symbol)
                            else:
                                df_hl_klines = get_hyperliquid_klines(symbol,interval=chart_interval)
                            df_hl_klines['timestamp'] = pd.to_datetime(df_hl_klines['timestamp'], unit='ms') 
                            df_hl = fetch_hl_fills(address)
                            df_hl = df_hl[df_hl['symbol'] == symbol]
                            df_hl['timestamp'] = pd.to_datetime(df_hl['timestamp'], unit='ms')
                            chart = create_interactive_chart(df_hl_klines, df_hl, width=1000, height=600)
                            st.altair_chart(chart)
                            
                           

            case "Position Lookups":
                exchange = st.selectbox("Select an Exchange",['Drift',"Hyperliquid"])
                address = st.text_input(label = "Enter Address", placeholder = "0x00")
                if len(address) >0:
                    if exchange == "Hyperliquid":
                        st.write(fetch_hl_positions(lookup=address))
                    elif exchange == "Drift":
                        st.write(asyncio.run(drift_pos_lookup(authority=address)))

            case "Backtester":
                st.title("Coming Soon")

            case "Orderbook Snapshots":
                exchange = st.selectbox("Select and Exchange", ['Hyperliquid','Vertex','Zeta Markets'])
                selected_symbol = st.selectbox("Choose a ticker",['BTC','ETH','SOL'])


                def style_dataframe(df):
                    return df.style.\
                        applymap(color_green, subset=['bid_price', 'bid_size']).\
                        applymap(color_red, subset=['ask_price', 'ask_size']).\
                    to_html()

               
                match exchange :
                    case "Hyperliquid" :
                        
                        styled_html = style_dataframe(fetch_hyperliquid_ob_snap(symbol=selected_symbol))
                        st.write(styled_html, unsafe_allow_html=True)
                        
                    case "Vertex":
                        styled_html = style_dataframe(fetch_vertex_ob_snap(symbol=selected_symbol))
                        st.write(styled_html, unsafe_allow_html=True)
                        
                    case "Zeta Markets":
                        styled_html = style_dataframe(fetch_zeta_orderbook_snap(symbol=selected_symbol))
                        st.write(styled_html, unsafe_allow_html=True)

            case "Consolidated Orderbook Density":
                st.warning("This is still buggy and regularly only shows bids")
                symbol_selection = st.selectbox("Select a token",['SOL',"BTC","ETH","ARB","APT","LTC"])

                data = aggregate_orderbooks(symbol=symbol_selection)
                df = pd.DataFrame(data)

                st.title("Consolidated Order Book Density")

                # Define the color scale based on bid/ask
                color_scale = alt.Scale(domain=['Bid', 'Ask'], range=['green', 'red'])

                # Plot bids
                bids_chart = alt.Chart(df).mark_circle().encode(
                    y=alt.Y('price:Q', title='Price', sort='ascending'),
                    x=alt.X('total_bid_size:Q', title='Size'),
                    color=alt.value('green'),
                    size=alt.Size('total_bid_size:Q', legend=None),
                    tooltip=['price', 'total_bid_size', 'bid_protocol']
                ).transform_filter(
                    alt.datum.total_bid_size > 0  # Filter out zero size bids
                )

                # Plot asks
                asks_chart = alt.Chart(df).mark_circle().encode(
                    y=alt.Y('price:Q', title=None, sort='ascending'),  # Title set to None to avoid duplication
                    x=alt.X('total_ask_size:Q', title=None),  # Title set to None to avoid duplication
                    color=alt.value('red'),
                    size=alt.Size('total_ask_size:Q', legend=None),
                    tooltip=['price', 'total_ask_size', 'ask_protocol']
                ).transform_filter(
                    alt.datum.total_ask_size > 0  # Filter out zero size asks
                )

                # Combine bids and asks chart
                combined_chart = (bids_chart + asks_chart).resolve_scale(
                    x='independent'  # Allows bids and asks to have independent x-axes
                ).interactive()

                # Displaying the chart in Streamlit
                st.altair_chart(combined_chart)
                                        
     case "Useful Links":
        st.title("Useful Links")
        
        st.markdown("""
        - [Vybe Network](https://www.vybenetwork.com/)
        - [Defillama](https://defillama.com/)
        - [Drift streamlit Dash](https://driftv2.streamlit.app/?tab=Welcome)
        - [Dirty Diggler's Dune Dash] (https://dune.com/dirt_diggler/the-great-solana-dashboard)
        """)
        st.markdown("""
                If you want to support the development of this dash and are not a resident of any restricted country, feel free to 
                use the ref links below. Ref Links are not endorsements ofcourse.
        - [Binance](http://binance.com/en/register?ref=TreeOfAlpha)
        - [Bybit](http://partner.bybit.com/b/Tree_Of_Alpha)
        - [Hyperliquid](https://app.hyperliquid.xyz/join/LIQ)
        - [Vertex](https://app.vertexprotocol.com?referral=uzpAPriz8z)
        """)

if __name__ == "__main__":
    main()
