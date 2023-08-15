from controller.controller import Controller
from Utils.utils import Utils
import os
import sys
import logging
import pandas as pd
from math import ceil
import threading
import time
from datetime import datetime


class SuperScreenerStrategy:
    def __init__(self):
        self.config = Utils.get_config()
        self.obj = Controller.brokerLogin

    def run_strategy(self):
        self.read_ss_stocks()
        self.capital_per_stock = round(self.config['capital'], 0)
        logging.info(f"Sleeping till {self.config['strategy_entry_time']}")
        Utils.sleep_until_time(self.config['strategy_entry_time'])
        self.execute_strategy_for_symbols()

    def calculate_quantities(self):
        # TODO
        pass

    def place_order(self, signal, entry_price):
        buffer_entry = self.config['buffer_entry']
        buffer_trigger = self.config['buffer_trigger']
        stop_loss = self.config['stop_loss']
        target1 = self.config['target1']
        target2 = self.config['target2']
        target3 = self.config['target3']
        dir = 1 if signal == "buy" else -1
        opp = -1 if signal == "buy" else 1
        trigger_price = round(entry_price - buffer_trigger if dir == -
                              1 else entry_price + buffer_trigger, 2)
        buffer = Utils.round_to_paise(entry_price, dir * buffer_entry)
        order_price = max(buffer, trigger_price) if dir == 1 else min(
            buffer, trigger_price)
        logging.debug(
            f"order_price:{order_price}= trigger_price:{trigger_price} or buffer:{buffer}")
        stop_loss_price = Utils.round_to_paise(entry_price, opp * stop_loss)
        logging.debug(
            f"stop_loss_price:{stop_loss_price} / stop_loss: {opp * stop_loss}")
        target1_price = Utils.round_to_paise(entry_price, dir * target1)
        logging.debug(
            f"target1_price: {target1_price} / target1: {dir * target1} ")
        target2_price = Utils.round_to_paise(entry_price, dir * target2)
        logging.debug(
            f"target2_price: {target2_price} / target2: {dir * target2} ")
        target3_price = Utils.round_to_paise(entry_price, dir * target3)
        logging.debug(
            f"target3_price: {target3_price} / target3: {dir * target3} ")
        return order_price, trigger_price, stop_loss_price, target1_price, target2_price, target3_price

    def order_status(self, entry_order_id):
        entry_order_status = "FAILED"
        try:
            orders = pd.DataFrame(self.obj.get_order_book())
            entry_order_status = orders[orders.norenordno ==
                                        entry_order_id]['status'].values[0]
            if entry_order_status == "REJECTED":
                rejection_reason = orders[orders.norenordno ==
                                          entry_order_id]['rejreason']
                logging.info(
                    f"Order rejected with reason : {rejection_reason}. Exiting the code")
        except Exception as e:
            logging.warning(f"{str(e)} error while checking order status")
        finally:
            return entry_order_status

    def execute_strategy(self, stock_data, capital_per_stock):
        logging.info(stock_data)
        symbol = stock_data['Stock']
        signal = stock_data['Signal']
        symbol_token_mapping = pd.read_csv(
            '../data/symbol_token_mapping.csv').set_index('symbol')['token'].to_dict()
        token = symbol_token_mapping.get(symbol)
        resp = self.obj.get_quotes("NSE", str(token))
        ltp = float(resp['lp'])
        total_quantity = round(capital_per_stock / ltp, 0)
        target1_quantity = ceil(
            total_quantity * self.config['target1_quantity_pct'])
        target2_quantity = ceil(
            (total_quantity - target1_quantity) * (self.config['target2_rem_quantity_pct']))
        target3_quantity = total_quantity - target1_quantity - target2_quantity
        if (
            target1_quantity == 0
            or (target2_quantity == 0)
            or (target3_quantity == 0)
        ):
            logging.warning(
                f"{symbol} t3:{target3_quantity}  = ttl_q:{total_quantity}  - t1q: {target1_quantity} - t2q:{target2_quantity} INVALID QTY")
            return
        elif signal == 'buy':
            entry_price = stock_data['High']
            order_price, trigger_price, stop_loss_price, target1_price, target2_price, target3_price = self.place_order(
                signal, entry_price)
            opposite_trans_type = self.obj.TRANSACTION_TYPE_SELL
            logging.info(
                f"placing BUY {symbol} {total_quantity}q  trgr:{trigger_price} prc:{order_price}")
            entry_order_id = self.obj.place_order(buy_or_sell="B", product_type="I",
                                                  exchange="NSE", tradingsymbol=symbol + "-EQ",
                                                  discloseqty=total_quantity,
                                                  quantity=total_quantity, price_type="SL-LMT",
                                                  retention='DAY',
                                                  price=order_price,
                                                  trigger_price=trigger_price)
            if (
                entry_order_id is not None
                and isinstance(entry_order_id, dict)
            ):
                logging.debug(
                    f"BUY {symbol} {total_quantity}Q  trgr:{trigger_price} prc:{order_price}")
            else:
                logging.warning(
                    f"FAILED buy {symbol} {total_quantity}Q  trgr:{trigger_price} prc:{order_price}")
                return
        elif signal == 'sell':
            entry_price = stock_data['Low']
            order_price, trigger_price, stop_loss_price, target1_price, target2_price, target3_price = self.place_order(
                signal, entry_price)
            opposite_trans_type = self.obj.TRANSACTION_TYPE_BUY
            logging.info(
                f"placing SELL {symbol} {total_quantity}Q  trgr:{trigger_price} prc:{order_price}")
            entry_order_id = self.obj.place_order(buy_or_sell="S", product_type="I",
                                                  exchange="NSE", tradingsymbol=symbol + "-EQ",
                                                  discloseqty=total_quantity,
                                                  quantity=total_quantity, price_type="SL-LMT",
                                                  retention='DAY',
                                                  price=order_price,
                                                  trigger_price=trigger_price)
            if (
                entry_order_id is not None
                and isinstance(entry_order_id, dict)
            ):
                logging.debug(
                    f"SELL {symbol} {total_quantity}Q  trgr:{trigger_price} prc:{order_price}")
            else:
                logging.warning(
                    f"FAILED sell {symbol} {total_quantity}Q  trgr:{trigger_price} prc:{order_price}")
                return
        exit_flag = False
        while not exit_flag:
            entry_order_status = self.order_status(
                entry_order_id['norenordno'])
            print(
                f"checking ..if {symbol} {signal}#{entry_order_id['norenordno']}/{total_quantity}Q for {order_price} is filled")
            if entry_order_status in ["CANCELED", "FAILED", "REJECTED"]:
                exit_flag = True
            elif entry_order_status == "COMPLETE":
                oco_order_id1 = self.obj.place_gtt_oco_mkt_order(
                    symbol + "-EQ",
                    "NSE",
                    max(target1_price, stop_loss_price),
                    min(target1_price, stop_loss_price),
                    opposite_trans_type,
                    self.obj.PRODUCT_TYPE_INTRADAY,
                    target1_quantity,
                )
                logging.info(
                    f"{symbol} Oco#1 {oco_order_id1} tgt:{target1_price} sl:{stop_loss_price} qty:{target1_quantity}")
                oco_order_id2 = self.obj.place_gtt_oco_mkt_order(
                    symbol + "-EQ",
                    "NSE",
                    max(target2_price, stop_loss_price),
                    min(target2_price, stop_loss_price),
                    opposite_trans_type,
                    self.obj.PRODUCT_TYPE_INTRADAY,
                    target2_quantity,
                )
                logging.info(
                    f"{symbol} Oco#2 {oco_order_id2} tgt:{target2_price} sl:{stop_loss_price} qty:{target2_quantity}")
                oco_order_id3 = self.obj.place_gtt_oco_mkt_order(
                    symbol + "-EQ",
                    "NSE",
                    max(target3_price, stop_loss_price),
                    min(target3_price, stop_loss_price),
                    opposite_trans_type,
                    self.obj.PRODUCT_TYPE_INTRADAY,
                    target3_quantity,
                )
                logging.info(
                    f"{symbol} Oco#3 {oco_order_id3} tgt:{target3_price} sl:{stop_loss_price} qty:{target3_quantity}")
                break
            else:
                time.sleep(5)
        # Keep checking order status for target 2 order, if executed than trail stop-loss of oco_order_id3
        while not exit_flag:
            # TODO
            logging.info(f"Checking {symbol} for OCO#2 hit.")
            exit_flag = True

    def read_ss_stocks(self):
        # today_date = pd.Timestamp.now().strftime('%Y%m%d')
        today_date = datetime.now().strftime("%Y_%m_%d")
        file_path = os.path.join(
            '../data/', f'super_screener_shortlisted_{today_date}.csv')
        if os.path.isfile(file_path):
            print(f"Found {file_path}")
            try:
                df = pd.read_csv(file_path)
                if df.empty:
                    logging.info(
                        "No stocks for Super Screener Strategy. Exiting the code.")
                    sys.exit()
                else:
                    self.ss_stocks = df.to_dict('records')
            except pd.errors.EmptyDataError:
                logging.info("The CSV file is empty. Exiting the code.")
                sys.exit()
            except Exception as e:
                logging.error(f"An error occurred while reading the CSV: {e}")
                sys.exit()
        else:
            print("Shortlisted file not found. Exiting the code.")
            sys.exit()

    def execute_strategy_for_symbols(self):
        threads = []
        for stock_data in self.ss_stocks:
            thread = threading.Thread(target=self.execute_strategy, args=(
                stock_data, self.capital_per_stock))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()
