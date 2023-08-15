#!/bin/python
from Utils.utils import Utils

config = Utils.get_config()


def print_config(**kwargs):
    for k, v in kwargs.items():
        print(f"{k}: {v} \n")


print(config)
buffer_entry = config['buffer_entry']
buffer_trigger = config['buffer_trigger']
stop_loss = config['stop_loss']
target1 = config['target1']
target2 = config['target2']
target3 = config['target3']

"""
 get entry_price as input from user"
"""
signal = "sell"
entry_price = 999.95

dir = 1 if signal == "buy" else -1
opp = -1 if signal == "buy" else 1
print("entry_price: ", entry_price)
trigger_price = round(entry_price - buffer_trigger if dir == -
                      1 else entry_price + buffer_trigger, 2)
buffer = Utils.round_to_paise(entry_price, dir * buffer_entry)
order_price = max(buffer, trigger_price) if dir == 1 else min(
    buffer, trigger_price)
print(
    f"order_price:{order_price}= trigger_price:{trigger_price} or buffer:{buffer}")
stop_loss_price = Utils.round_to_paise(entry_price, opp * stop_loss)
print(f"stop_loss_price:{stop_loss_price} / stop_loss: {opp * stop_loss}")
target1_price = Utils.round_to_paise(entry_price, dir * target1)
print(f"target1_price: {target1_price} / target1: {dir * target1} ")
target2_price = Utils.round_to_paise(entry_price, dir * target2)
print(f"target2_price: {target2_price} / target2: {dir * target2} ")
# write testcase for trigger_price and order_price
if signal == "sell":
    assert trigger_price < entry_price, 'trigger price should be less than entry price for SELL'
    assert buffer <= order_price, 'buffer should be less than order price for SELL'
    assert order_price < trigger_price, 'order price should be less than trigger for SELL'
elif signal == "buy":
    assert trigger_price > entry_price, 'trigger price should be greater than entry price for BUY'
    assert buffer >= order_price, 'buffer should be greater than order price for BUY'
    assert order_price > trigger_price, 'order price should be greater than trigger for BUY'
