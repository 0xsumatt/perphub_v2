import yfinance as yf
import pandas_datareader as pd_dtr
yf.pdr_override()

class beta_calculator():

    def __init__(self, ticker_1, ticker_2, start_date, end_date):
        # If ticker_1 is a single string asset, convert it to a list
        if isinstance(ticker_1, str):
            self.ticker_1 = [ticker_1]
        else:
            self.ticker_1 = ticker_1
        self.ticker_2 = ticker_2
        self.start_date = start_date
        self.end_date = end_date

    def calc_beta(self):
        
        df_ticker_1 = None
        for ticker in self.ticker_1:
            prices = yf.download(ticker, start=self.start_date, end=self.end_date)
            daily_returns = prices['Adj Close'].pct_change()[1:]

            
            if df_ticker_1 is None:
                df_ticker_1 = daily_returns
            else:
                df_ticker_1 += daily_returns

    
        if len(self.ticker_1) > 1:
            df_ticker_1 /= len(self.ticker_1)

   
        price_ticker_2 = yf.download(self.ticker_2, start=self.start_date, end=self.end_date)
        ticker_2_daily = price_ticker_2['Adj Close'].pct_change()[1:]

        cov = ticker_2_daily.cov(df_ticker_1)
        var = df_ticker_1.var()
        beta = cov / var

        return beta

