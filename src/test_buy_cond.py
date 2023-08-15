import json
from datetime import date
import pandas as pd

today = date.today().strftime("%Y_%m_%d")
file_path = f"../data/stocks_with_pivots_{today}.csv"
# file_path = "../data/stocks_with_pivots_2023_08_01.csv"
stock_details_df = pd.read_csv(file_path)
symbol_token_mapping = pd.read_csv(
    '../data/symbol_token_mapping.csv').set_index('symbol')['token'].to_dict()

with open("../data/ohlc.json", "r") as file:
    ohlc = json.load(file)

lst_signals = []
for symbol in stock_details_df['symbol'].unique():
    if ohlc.get(symbol) is None:
        print(f"{symbol} is not found skipping ...")
        continue
    open_price = ohlc[symbol][0]
    high = ohlc[symbol][1]
    low = ohlc[symbol][2]
    ltp = ohlc[symbol][3]
    prev_day_details = stock_details_df[stock_details_df['symbol']
                                        == symbol].iloc[-1]
    try:
        # Assuming you have the necessary variables defined:
        # open_price, low, ltp, prev_day_details, high
        # Condition 1
        if (
            open_price == low
            and ltp > prev_day_details['prev_high']
            and ltp >= prev_day_details['RES1']
            and ltp < prev_day_details['RES3']
            and prev_day_details['percent_return'] <= 3
            and high < (prev_day_details['RES3'] - (prev_day_details['RES3'] * 0.006))
        ):
            print(f"BUY \n {prev_day_details}\n OHLC:{ohlc[symbol]}")
        else:
            print(f"{symbol}")
            assert open_price == low, "Condition 1 failed: open_price is not equal to low."
# Condition 2
            assert ltp > prev_day_details['prev_high'], "Condition 2 failed: ltp is not greater than prev_day_details['prev_high']."
# Condition 3
            assert ltp >= prev_day_details['RES1'], "Condition 3 failed: ltp is not greater than or equal to prev_day_details['RES1']."
# Condition 4
            assert ltp < prev_day_details['RES3'], "Condition 4 failed: ltp is not less than prev_day_details['RES3']."
# Condition 5
            assert prev_day_details['percent_return'] <= 3, "Condition 5 failed: prev_day_details['percent_return'] is not less than or equal to 3."
            assert high < (prev_day_details['RES3'] - (prev_day_details['RES3'] * 0.006)
                           ), "Condition 6 failed: high is not less than prev_day_details['RES3'] - (prev_day_details['RES3'] * 0.006))."
    except Exception as e:
        print(e)
