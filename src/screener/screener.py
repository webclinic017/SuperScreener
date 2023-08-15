import time
import logging
from datetime import date, timedelta, datetime,  time as dt_time
from controller.controller import Controller
import pandas as pd
from tqdm import tqdm
import os
from Utils.utils import Utils
import json
import urllib.parse
# import yfinance as yf


class Screener:
    def __init__(self, stock_symbols):
        self.stock_symbols = stock_symbols
        self.short_listed_stocks = []
        self.obj = Controller.brokerLogin
        self.broker_name = Controller.brokerName

    def write_dict_to_json(self, file_path, data):
        folder_path = os.path.dirname(file_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        json_string = json.dumps(data, indent=4)
        with open(file_path, "w") as file:
            file.write(json_string)
        print("JSON data has been written to the file:", file_path)

    def getEpoch(self, datetimeObj=None):
        # This method converts given datetimeObj to epoch seconds
        if datetimeObj == None:
            datetimeObj = datetime.now()
        epochSeconds = datetime.timestamp(datetimeObj)
        return int(epochSeconds)  # converting double to long

    def _get_sym_tok_mapping(self):
        logging.info("Mapping symbol to token..")
        today = date.today()
        last_run_file = "../data/last_run_date.txt"
        if os.path.exists(last_run_file):
            with open(last_run_file, "r") as file:
                last_run_date_str = file.read()
                last_run_date = date.fromisoformat(last_run_date_str)

                if last_run_date == today:
                    logging.info(
                        "Mapping has already been run today. Skipping refresh.")
                    mapping_df = pd.read_csv(
                        "../data/symbol_token_mapping.csv")
                    self.symbol_token_mapping = mapping_df
                    return
        universe_df = pd.read_csv("../data/universe.csv")
        symbol_to_token = {}
        for symbol in universe_df["Symbol"]:
            # token = self.obj.instrument_symbol("NSE", symbol + "-EQ")
            # symbol_to_token[symbol] = token
            resp = self.obj.searchscrip(
                exchange='NSE', searchtext=symbol + "-EQ")
            token = resp['values'][0]['token']
            symbol_to_token[symbol] = token

        # Store the symbol-to-token mapping in a file
        mapping_file = "../data/symbol_token_mapping.csv"
        mapping_df = pd.DataFrame(
            symbol_to_token.items(), columns=["symbol", "token"])
        self.symbol_token_mapping = mapping_df
        mapping_df.to_csv(mapping_file, index=False)
        # Update the last run date
        with open(last_run_file, "w") as file:
            file.write(str(today))

        logging.info("Symbol to token mapping is refreshed.")

    def get_next_trading_day(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        holidays_df = pd.read_csv("config/holidays.csv")
        holidays = set(holidays_df["date"])
        while tomorrow.weekday() in (5, 6) or tomorrow.strftime("%Y-%m-%d") in holidays:
            tomorrow += timedelta(days=1)
        return tomorrow.strftime('%Y_%m_%d')

    def _check_last_run(self):
        current_date = datetime.now().strftime("%Y_%m_%d")
        filename = f"data/stocks_with_pivots_{current_date}.csv"
        if os.path.exists(filename):
            return True
        else:
            return False

    def run_scan(self):
        if not self._check_last_run():
            logging.info("Running scan...")
            self._get_sym_tok_mapping()
            logging.info("Calculating pivots on previous day's data.")
            for symbol in tqdm(self.stock_symbols, desc="Processing", unit="symbol"):
                stock_data = self.fetch_stock_data(symbol)
                if stock_data.shape[0] == 0:
                    logging.warning(f"No data found for {symbol}.")
                else:
                    percent_return = self._calc_perc_ret(stock_data)
                    prev_close = stock_data['Close'].iloc[-1]
                    prev_high = stock_data['High'].iloc[-1]
                    prev_low = stock_data['Low'].iloc[-1]
                    pivot_points = self._calc_pivot(stock_data)

                    stock_dict = {
                        'symbol': symbol,
                        'percent_return': percent_return,
                        'prev_high': prev_high,
                        'prev_low': prev_low,
                        'prev_close': prev_close,
                        **pivot_points
                    }
                    self.short_listed_stocks.append(stock_dict)
                    time.sleep(0.01)
            logging.info("Pivot calculation completed.")
        else:
            logging.info("Pivot calculation is already present.")
            current_date = datetime.now().strftime("%Y_%m_%d")
            df = pd.read_csv(os.path.join(
                "../data", f"stocks_with_pivots_{current_date}.csv")).to_dict('records')
            self.short_listed_stocks = df
        self._proc_shortlist_stocks(self.short_listed_stocks)
        signals = self.check_entry_rule()
        self.save_signals(signals)
        logging.info(signals)

    def save_signals(self, signals):
        df_signal = pd.DataFrame(signals)
        current_date = datetime.now().strftime("%Y_%m_%d")
        df_signal.to_csv(os.path.join(
            "../data", f"super_screener_shortlisted_{current_date}.csv"), index=False)

    def _proc_shortlist_stocks(self, short_listed_stocks):
        df = pd.DataFrame(short_listed_stocks)
        current_date = datetime.now().strftime("%Y_%m_%d")
        df.to_csv(os.path.join(
            "../data", f"stocks_with_pivots_{current_date}.csv"), index=False)

    def fetch_stock_data(self, symbol):
        symbol_eq = symbol  # + "-EQ"  # Add "-EQ" to the symbol
        encoded_symbol = urllib.parse.quote(symbol_eq + "-EQ")
        token = self.symbol_token_mapping.loc[self.symbol_token_mapping["symbol"]
                                              == symbol_eq, "token"].values[0]
        current_time = datetime.now().time()
        end_date = date.today()
        start_date = end_date - timedelta(days=7)  # 7 days before the end date
        start_datetime = datetime.combine(start_date, dt_time.min)
        end_datetime = datetime.combine(end_date, dt_time.max)
        end_datetime -= timedelta(days=1)  # Yesterday's date
        exchange = "NSE"
        start_datetime = self.getEpoch(start_datetime)
        end_datetime = self.getEpoch(end_datetime)
        try:
            quote_history = self.get_history(exchange, str(
                token), encoded_symbol, start_datetime, end_datetime)
        except Exception as e:
            logging.warning(f"Got {e} while fetching data for {symbol}")
            time.sleep(2)
        stock_data = self.process_history_data(quote_history)
        return stock_data

    def read_quote(self, exchange, token):
        # self.obj.get_quotes("NSE",token)
        max_retries = 3
        retry_delay = 5
        for retry in range(max_retries):
            try:
                resp = self.obj.get_quotes(exchange, token)
                if not resp['stat'] == "Ok":
                    logging.warning(f"No data found for {token}")
                    time.sleep(retry_delay)
                else:
                    if not "o" in resp.keys():
                        logging.warning(
                            f"Open data not found for {token}..Retrying")
                        time.sleep(retry_delay)
                    elif not "lp" in resp.keys():
                        logging.warning(
                            f"LTP data not found for {token}..Retrying")
                        time.sleep(retry_delay)
                    elif not "l" in resp.keys():
                        logging.warning(
                            f"Low data not found for {token}..Retrying")
                        time.sleep(retry_delay)
                    elif not "h" in resp.keys():
                        logging.warning(
                            f"High data not found for {token}..Retrying")
                        time.sleep(retry_delay)
                    else:
                        return resp
            except Exception as e:
                logging.warning(
                    f"Error occurred while fetching data for {token}: {str(e)}")
                time.sleep(retry_delay)

    def get_history(self, exchange, token, symbol, start_datetime, end_datetime):
        logging.debug("Running fuction get_history.")
        max_retries = 3
        retry_delay = 5
        for retry in range(max_retries):
            try:
                quote_history = self.obj.get_daily_price_series(
                    exchange, symbol, start_datetime, end_datetime)
                if len(quote_history) == 0:
                    logging.warning(f"No data found for {token}")
                    time.sleep(retry_delay)
                else:
                    logging.debug(
                        f"Total records recieved : {len(quote_history)}")
                    break
            except Exception as e:
                logging.warning(
                    f"Error occurred while fetching data for {token}: {str(e)}")
                time.sleep(retry_delay)
        return quote_history

    # def process_history_data(self, quote_history):
    #     columns=['time', 'into', 'inth', 'intl', 'intc', 'intv']
    #     df = pd.DataFrame(quote_history, columns=columns)
    #     df['time'] = pd.to_datetime(df['time'], format='%d-%m-%Y %H:%M:%S')
    #     df = df.rename(columns={'time': 'Date', 'into': 'Open', 'inth': 'High', 'intl': 'Low', 'intc': 'Close', 'intv': 'Volume'})
    #     unique_dates = df['Date'].dt.date.unique()
    #     df = df.set_index('Date')
    #     for c in ['Open','High','Low','Close']:
    #         df[c] = df[c].astype('float')
    #     df['Volume'] = df['Volume'].astype('int')
    #     df_daily = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    #     df_daily = df_daily.reset_index()
    #     df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    #     df_daily = df_daily[df_daily['Date'].dt.date.isin(unique_dates)]
    #     return df_daily
    def process_history_data(self, quote_history):
        quote_history = [json.loads(json_str) for json_str in quote_history]
        logging.debug("Running fuction process_history_data.")
        logging.debug(f"Total records recieved : {len(quote_history)}")
        columns = ['time', 'into', 'inth', 'intl', 'intc', 'ssboe', 'intv']
        df = pd.DataFrame(quote_history, columns=columns)
        logging.debug(f"Shape of dataframe is {df.shape}")
        df = df.drop(['ssboe'], axis=1)
        df['time'] = pd.to_datetime(df['time'], format='%d-%b-%Y')
        df = df.sort_values(by='time')
        df = df.rename(columns={'time': 'Date', 'into': 'Open',
                       'inth': 'High', 'intl': 'Low', 'intc': 'Close', 'intv': 'Volume'})
        # unique_dates = df['Date'].dt.date.unique()
        # df = df.set_index('Date')
        for c in ['Open', 'High', 'Low', 'Close']:
            df[c] = df[c].astype('float')
        # df['Volume'] = df['Volume'].astype('int')
        # df_daily = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        # df_daily = df_daily.reset_index()
        # df_daily['Date'] = pd.to_datetime(df_daily['Date'])
        # df_daily = df_daily[df_daily['Date'].dt.date.isin(unique_dates)]
        return df

    def _calc_perc_ret(self, stock_data):
        stock_data['Prev Close'] = stock_data['Close'].shift(1)
        stock_data['% Return'] = (
            stock_data['Close'] - stock_data['Prev Close']) / stock_data['Prev Close'] * 100
        return round(stock_data['% Return'].iloc[-1], 2)

    def _calc_pivot(self, stock_data):
        prev_high = stock_data['High'].iloc[-1]
        prev_low = stock_data['Low'].iloc[-1]
        prev_close = stock_data['Close'].iloc[-1]
        pivot = round((prev_high + prev_low + prev_close) / 3, 2)
        res1 = round(2 * pivot - prev_low, 2)
        res2 = round(pivot + (res1 - (2 * pivot - prev_high)), 2)
        res3 = round(prev_high + 2 * (pivot - prev_low), 2)
        sup1 = round(2 * pivot - prev_high, 2)
        sup2 = round(pivot - (res1 - sup1), 2)
        sup3 = round(prev_low - 2 * (prev_high - pivot), 2)

        pivot_points = {
            'prev_high': prev_high,
            'prev_low': prev_low,
            'PIVOT': pivot,
            'RES1': res1,
            'RES2': res2,
            'RES3': res3,
            'SUP1': sup1,
            'SUP2': sup2,
            'SUP3': sup3
        }

        return pivot_points

    def check_entry_rule(self):
        today = date.today().strftime("%Y_%m_%d")
        file_path = f"../data/stocks_with_pivots_{today}.csv"
        stock_details_df = pd.read_csv(file_path)
        symbol_token_mapping = pd.read_csv(
            '../data/symbol_token_mapping.csv').set_index('symbol')['token'].to_dict()
        config = Utils.get_config()
        start_time = config['strategy_start_time']
        current_time = datetime.now().strftime("%H:%M:%S")

        if current_time < start_time:
            sleep_time = datetime.strptime(
                start_time, "%H:%M:%S") - datetime.strptime(current_time, "%H:%M:%S")
            time.sleep(sleep_time.total_seconds())

        lst_signals = []
        data = {}
        for symbol in stock_details_df['symbol'].unique():
            dir_result = {}
            token = str(symbol_token_mapping.get(symbol))
            exchange = "NSE"
            resp = self.read_quote(exchange, token)
            if (
                resp is None
                or not isinstance(resp, dict)
            ):
                break
            open_price = float(resp['o'])
            ltp = float(resp['lp'])
            low = float(resp['l'])
            high = float(resp['h'])
            prev_day_details = stock_details_df[stock_details_df['symbol']
                                                == symbol].iloc[-1]
            if (
                open_price == low
                and ltp > prev_day_details['prev_high']
                and ltp >= prev_day_details['RES1']
                and ltp < prev_day_details['RES3']
                and prev_day_details['percent_return'] <= 3
                and high < (prev_day_details['RES3'] - (prev_day_details['RES3'] * 0.006))
            ):
                dir_result['Stock'] = symbol
                dir_result['Signal'] = 'buy'
                dir_result['High'] = high
                dir_result['Low'] = low
                dir_result['Close'] = ltp
                lst_signals.append(dir_result)
            elif (
                open_price == high
                and ltp < prev_day_details['prev_low']
                and ltp < prev_day_details['SUP1']
                and ltp > prev_day_details['SUP3']
                and prev_day_details['percent_return'] >= -3
                and low > (prev_day_details['SUP3'] + (prev_day_details['SUP3'] * 0.006))
            ):
                dir_result['Stock'] = symbol
                dir_result['Signal'] = 'sell'
                dir_result['High'] = high
                dir_result['Low'] = low
                dir_result['Close'] = ltp
                lst_signals.append(dir_result)
            data[symbol] = [open_price, high, low, ltp]
        self.write_dict_to_json("../data/ohlc.json", data)
        return lst_signals
