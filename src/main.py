import logging
import pandas as pd
import sys

from Utils.utils import Utils
from controller.controller import Controller
from screener.screener import Screener
from strategy.strategies import SuperScreenerStrategy


def initLoggingConfg():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S")


initLoggingConfg()

config = Utils.get_config()
# Commenting following cod to run on weekend.
if Utils.isTodayHoliday():
    logging.info(
        "Today is a weekend or holiday. Skipping the execution of the code.")
    sys.exit()

universe_df = pd.read_csv('../data/universe.csv')
universe_df['Disabled'] = universe_df['Disabled'].astype('str')
universe_df = universe_df[~(universe_df.Disabled.str.upper() == 'Y')]
stock_symbols = universe_df['Symbol'].tolist()
stock_symbols = list(map(str.strip, stock_symbols))

controller = Controller()
controller.generate_login_object()
screener = Screener(stock_symbols)
screener.run_scan()

ss = SuperScreenerStrategy()
ss.run_strategy()
