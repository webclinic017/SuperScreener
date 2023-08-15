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


if __name__ == "__main__":
    try:
        order_no = input("Enter order no: ")
        resp = api.cancel_order(order_no)
        print(resp)
        orders = pd.DataFrame(api.get_order_book())
        print(orders)
        api.logout()
    except Exception as e:
        print(f"Error in main: {str(e)}")
