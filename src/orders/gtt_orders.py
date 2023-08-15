def gtt_orders(api):
    lst = []
    dct = {}
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


def is_open(main_dict, alert_id):
    return any(alert_id in sub_dict.values() for sub_dict in main_dict.values() if isinstance(sub_dict, dict))


def cancel_order(api, alert_id):
    print(f'Cancelled GTT Order/Alert :: {api.cancelgtt(alert_id)}')


def modify_order(
    api,
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
    return alert_id


def oco(
    api,
    tradingsymbol: str,
    exchange: str,
    alert_price_above_1: float,
    alert_price_below_2: float,
    buy_or_sell: str,  # 'B' or 'S'
    product_type: str,  # 'I' Intraday, 'C' Delivery, 'M' Normal Margin for options
    quantity: int,
    remarks: str,
):
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
    return alert_id
