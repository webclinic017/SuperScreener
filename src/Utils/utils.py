import math
import logging
import uuid
import time
import calendar
from datetime import datetime, timedelta, date
import pytz
import os
import yaml
import pandas as pd
from decimal import Decimal, ROUND_HALF_EVEN, getcontext

# from config.Config import getHolidays
# from models.Direction import Direction
# from trademgmt.TradeState import TradeState


class Utils:
    dateFormat = "%Y-%m-%d"
    timeFormat = "%H:%M:%S"
    dateTimeFormat = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def initLoggingConfig():
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%Y-%m-%d %H:%M:%S")

    @staticmethod
    def roundtoNSEPrice(price):
        x = round(price, 2) * 20
        y = math.ceil(x)
        return y / 20

    @staticmethod
    def get_config():
        # Read the threshold values from the YAML file
        # root_dir = os.path.dirname(os.path.dirname(__file__))
        # yaml_path = os.path.join(root_dir, 'config', 'config.yaml')
        # with open(yaml_path, 'r') as yaml_file:
        #     config = yaml.safe_load(yaml_file)
        config_file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../../config/config.yaml"))
        with open(config_file_path, 'r') as yaml_file:
            config = yaml.safe_load(yaml_file)
            return config

    @staticmethod
    def isMarketOpen():
        if Utils.isTodayHoliday():
            return False
        now = datetime.now()
        marketStartTime = Utils.getMarketStartTime()
        marketEndTime = Utils.getMarketEndTime()
        return now >= marketStartTime and now <= marketEndTime

    @staticmethod
    def getMarketStartTime(dateTimeObj=None):
        return Utils.getTimeOfDay(9, 15, 0, dateTimeObj)

    @staticmethod
    def getMarketEndTime(dateTimeObj=None):
        return Utils.getTimeOfDay(15, 30, 0, dateTimeObj)

    @staticmethod
    def getTimeOfDay(hours, minutes, seconds, dateTimeObj=None):
        if dateTimeObj == None:
            dateTimeObj = datetime.now()
        dateTimeObj = dateTimeObj.replace(
            hour=hours, minute=minutes, second=seconds, microsecond=0)
        return dateTimeObj

    @staticmethod
    def getTimeOfToDay(hours, minutes, seconds):
        return Utils.getTimeOfDay(hours, minutes, seconds, datetime.now())

    @staticmethod
    def getTodayDateStr():
        return Utils.convertToDateStr(datetime.now())

    @staticmethod
    def convertToDateStr(datetimeObj):
        return datetimeObj.strftime(Utils.dateFormat)

    @staticmethod
    def getEpoch(datetimeObj=None):
        # This method converts given datetimeObj to epoch seconds
        if datetimeObj == None:
            datetimeObj = datetime.now()
        epochSeconds = datetime.timestamp(datetimeObj)
        return int(epochSeconds)  # converting double to long

    @staticmethod
    def isMarketClosedForTheDay():
        # This method returns true if the current time is > marketEndTime
        # Please note this will not return true if current time is < marketStartTime on a trading day
        if Utils.isTodayHoliday():
            return True
        now = datetime.now()
        marketEndTime = Utils.getMarketEndTime()
        return now > marketEndTime

    @staticmethod
    def waitTillMarketOpens(context):
        nowEpoch = Utils.getEpoch(datetime.now())
        marketStartTimeEpoch = Utils.getEpoch(Utils.getMarketStartTime())
        waitSeconds = marketStartTimeEpoch - nowEpoch
        if waitSeconds > 0:
            logging.info(
                "%s: Waiting for %d seconds till market opens...", context, waitSeconds)
            time.sleep(waitSeconds)

    @staticmethod
    def sleep_until_time(target_time):
        logging.info(f"Sleeping till {target_time}.")
        target_time = datetime.strptime(target_time, '%H:%M:%S').time()
        current_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_diff = datetime.combine(
            date.today(), target_time) - datetime.combine(date.today(), current_time)
        sleep_duration = time_diff.total_seconds()

        logging.info(f"Sleeping for {sleep_duration} seconds.")
        if sleep_duration > 0:
            time.sleep(sleep_duration)
        # logging.info("Target time reached. Continue with the rest of the code.")

    @staticmethod
    def isHoliday(datetimeObj):
        dayOfWeek = calendar.day_name[datetimeObj.weekday()]
        if dayOfWeek == 'Saturday' or dayOfWeek == 'Sunday':
            return True

        dateStr = Utils.convertToDateStr(datetimeObj)
        holidays = Utils.getHolidays()
        if (dateStr in holidays):
            return True
        else:
            return False

    @staticmethod
    def getHolidays():
        holidays_file = os.path.join("../config", "holidays.csv")
        holidays_df = pd.read_csv(holidays_file)
        holidays = holidays_df["date"].tolist()
        return holidays

    @staticmethod
    def isTodayHoliday():
        return Utils.isHoliday(datetime.now())

    @staticmethod
    def round_to_paise(buy_price, buffer_percent=0.5):
        buy_price_decimal = Decimal(str(buy_price))
        buffer_amount_decimal = buy_price_decimal * \
            (Decimal(str(buffer_percent)) / 100)
        pending_order_price = buy_price_decimal + buffer_amount_decimal
        pending_order_price_rounded = (
            pending_order_price * 20).quantize(1, rounding=ROUND_HALF_EVEN) / 20
        return float(pending_order_price_rounded)

    @staticmethod
    def multiply(big, sign, fraction):
        big = Decimal(str(big))
        return (big + (sign * Decimal(str(fraction))))


if __name__ == "__main__":
    utils = Utils()
    print(utils.multiply(600, -1, 0.05))
