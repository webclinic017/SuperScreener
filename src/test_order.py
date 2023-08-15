from NorenApi import NorenApi
import time
import pandas as pd
from toolkit.fileutils import Fileutils


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


def order_status(entry_order_id):
    entry_order_status = "FAILED"
    try:
        orders = pd.DataFrame(api.get_order_book())
        entry_order_status = orders[orders.norenordno ==
                                    entry_order_id]['status'].values[0]
        if entry_order_status == "REJECTED":
            rejection_reason = orders[orders.norenordno ==
                                      entry_order_id]['rejreason']
            print(
                f"Order rejected with reason : {rejection_reason}. Exiting the code")
    except Exception as e:
        print(f"{str(e)} error while checking order status")
    finally:
        return entry_order_status


if __name__ == "__main__":
    try:
        entry_order_id = api.place_order(buy_or_sell="B", product_type="I",
                                         exchange="NSE", tradingsymbol="AMARAJABAT-EQ",
                                         discloseqty=1,
                                         quantity=1, price_type="SL-LMT",
                                         retention='DAY',
                                         price=635.10,
                                         trigger_price=635.05)
        if (
            entry_order_id is not None
            and isinstance(entry_order_id, dict)
        ):
            print(
                f"BUY# {entry_order_id['norenordno']}"
            )
        else:
            entry_order_id = {
                'status': "FAILED"}
            print(
                "BUY entry order Failed")
        status = order_status(entry_order_id['norenordno'])
        print(status)
        print(type(status))
    except KeyboardInterrupt:
        api.logout()
    except Exception as e:
        print(f"Error in main: {str(e)}")
