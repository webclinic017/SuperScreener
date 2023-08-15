from NorenApi import NorenApi
import time
import pandas as pd
from toolkit.fileutils import Fileutils
from pprint import pprint
import json


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        original_return_val = func(*args, **kwargs)
        end = time.perf_counter()
        print("time elapsed in ", func.__name__, ": ", end - start, sep="")
        return original_return_val
    return wrapper


sec_dir = "../../../"
cred = Fileutils().get_lst_fm_yml(sec_dir + "SuperScreener.yaml")
print(cred)
# totp = f"{int(pyotp.TOTP(cred['factor2']).now()):06d}"
# start of our program
api = NorenApi(
    host="https://profitmax.profitmart.in/NorenWClientTP",
    websocket='wss://profitmax.profitmart.in/NorenWSTP/',
)

ret = api.login(
    userid=cred["uid"],
    password=cred["pwd"],
    twoFA=cred['factor2'],
    vendor_code=cred["vc"],
    api_secret=cred["app_key"],
    imei='1234'
)


@timing_decorator
def option_chain_example():
    data = api.get_option_chain("NFO", "NIFTY12JAN23P18000", "18000", count=30)
    print(data)
    df = pd.DataFrame(data["values"])
    print(df)
    print(df.tsym.values)


def gtt_orders():
    lst = []
    dct = {}
    try:
        resp = api.get_pending_gtt_orders()
        if (
            resp is not None
            and isinstance(resp, list)
            and len(resp) > 0
        ):
            for line in resp:
                if (
                    isinstance(line, dict)
                ):
                    dct[line['tsym']] = {'alert_id': line['al_id'], 'tradingsymbol': line['tsym'],
                                         'exchange': line['exch'], 'product_type': line['prd'],
                                         'buy_or_sell': line['trantype'], 'quantity': line['qty'],
                                         'alert_price_above_1': line['oivariable'][0]['d'],
                                         'alert_price_below_2': line['oivariable'][1]['d'],
                                         'remarks': line['remarks']
                                         }
                lst.append(dct)
        return lst
    except Exception as e:
        print(f"Error in orders: {str(e)}")


def gtt(B_or_S="S"):
    al_type = api.ALERT_TYPE_BELOW if B_or_S == "S" else api.ALERT_TYPE_ABOVE
    alert_id = api.place_gtt_order(
        "SBIN-EQ",
        "NSE",
        al_type,
        573.4,
        B_or_S,
        "I",
        5,
        "LMT",
        575.3,
        "checking gtt below",
    )
    print(f"Alert ID for GTT Order :: {alert_id}")


def _is_open(main_dict, alert_id):
    return any(alert_id in sub_dict.values() for sub_dict in main_dict.values() if isinstance(sub_dict, dict))


def cancel_order(alert_id):
    try:
        print(f'Cancelled GTT Order/Alert :: {api.cancelgtt(alert_id)}')
    except Exception as e:
        print(f"{e} while cancel_order")


def modify_order(
    alert_id: str,
    tradingsymbol: str,
    exchange: str,
    alert_price_above_1: float,
    alert_price_below_2: float,
    buy_or_sell: str,  # 'B' or 'S'
    product_type: str,  # 'I' Intraday, 'C' Delivery, 'M' Normal Margin for options
    quantity: int,
    remarks: str = "modified",
):
    try:
        alert_id = api.modify_gtt_oco_mkt_order(
            alert_id=alert_id,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            alert_price_above_1=alert_price_above_1,
            alert_price_below_2=alert_price_below_2,
            buy_or_sell=buy_or_sell,
            product_type=product_type,
            quantity=quantity,
            remarks=remarks
        )
        print(f"{tradingsymbol} with {alert_id} modified succcessfully")
    except Exception as e:
        print(f"{e} No GTT Order/Alert found")


def oco(
    tradingsymbol: str,
    exchange: str,
    alert_price_above_1: float,
    alert_price_below_2: float,
    buy_or_sell: str,  # 'B' or 'S'
    product_type: str,  # 'I' Intraday, 'C' Delivery, 'M' Normal Margin for options
    quantity: int,
    remarks: str,
):
    """
        tradingsymbol="SILVERMIC28FEB23",
        exchange="MCX",
        alert_price_above_1=69200.0,
        alert_price_below_2=9000.0,
        buy_or_sell=api.TRANSACTION_TYPE_SELL,
        product_type=api.PRODUCT_TYPE_INTRADAY,
        quantity=1,
        remarks="SuperScreener"
    """
    alert_id = api.place_gtt_oco_mkt_order(
        tradingsymbol=tradingsymbol,
        exchange=exchange,
        alert_price_above_1=alert_price_above_1,
        alert_price_below_2=alert_price_below_2,
        buy_or_sell=buy_or_sell,
        product_type=product_type,
        quantity=quantity,
        remarks=remarks
    )
    print(f"Alert ID for GTT OCO MKT Order :: {alert_id}")


if __name__ == "__main__":
    try:
        """
        oco(
            tradingsymbol="AMARAJABAT-EQ",
            exchange="NSE",
            alert_price_above_1=625,
            alert_price_below_2=615,
            buy_or_sell=api.TRANSACTION_TYPE_SELL,
            product_type=api.PRODUCT_TYPE_INTRADAY,
            quantity=1,
            remarks="SuperScreener"
        )
        modify_order(
            alert_id="23072000000592",
            tradingsymbol="BALRAMCHIN-EQ",
            exchange="NSE",
            alert_price_above_1=395,
            alert_price_below_2=385,
            buy_or_sell=api.TRANSACTION_TYPE_SELL,
            product_type=api.PRODUCT_TYPE_INTRADAY,
            quantity=1,
            remarks="SuperScreener"
        )
        cancel_order("23072100000378")
        {'stat': 'Ok', 'ai_t': 'LMT_BOS_O', 'al_id': '23080200000337', 'tsym': 'FEDERALBNK-EQ',
        'exch': 'NSE', 'token': '1023', 'remarks': '', 'validity': 'GTT', 'norentm': '11:34:49 02-08-2023',
        'pp': '2', 'ls': '1', 'ti': '0.05', 'brkname': 'PROFITMART', 'actid': '35660042', 'trantype': 'B',
        'prctyp': 'MKT', 'qty': 2, 'prc': '0.00', 'C': 'C', 'prd': 'I', 'ordersource': 'TT',
        'place_order_params': {'actid': '35660042', 'trantype': 'B', 'prctyp': 'MKT', 'qty': 2,
                            'prc': '0.00', 'C': 'C', 's_prdt_ali': 'MIS', 'prd': 'I', 'ordersource': 'TT'},
        'place_order_params_leg2': {'actid': '35660042', 'trantype': 'B', 'prctyp': 'MKT', 'qty': 2,
                                    'prc': '0.00', 'C': 'C', 'prd': 'I', 'ordersource': 'TT'},
        'd': '134.00', 'oivariable': [{'var_name': 'x', 'd': '134.00'}, {'var_name': 'y', 'd': '131.85'}]}
        """
        while True:
            lst = gtt_orders()
            pprint(lst)
            for dct in lst:
                if _is_open(dct, '23080200000358'):
                    print("success")
            time.sleep(2)
    except KeyboardInterrupt:
        api.logout()
    except Exception as e:
        print(f"Error in main: {str(e)}")
