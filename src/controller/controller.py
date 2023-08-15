from NorenApi import NorenApi


import logging
import yaml


class Controller:
    brokerLogin = None  # static variable
    brokerName = "Profitmart"  # static variable

    def load_credentials(self):
        logging.info("Loading credentials.")
        with open("../../../SuperScreener.yaml", "r") as file:
            credentials = yaml.safe_load(file)
        self.uid = credentials['uid']
        self.pwd = credentials['pwd']
        self.factor2 = credentials['factor2']
        self.vc = credentials['vc']
        self.app_key = credentials['app_key']

    def generate_login_object(self):
        logging.info("Creating login object....")
        self.load_credentials()
        # pmart = Finvasia(user_id=self.uid, password=self.pwd, pin=self.factor2,
        #          vendor_code=self.vc, app_key=self.app_key, imei="1234",
        #          broker="profitmart")
        # if pmart.authenticate():
        #     Controller.brokerLogin = pmart
        #     logging.info("Login object created successfully!!")

        api = NorenApi(
            host="https://profitmax.profitmart.in/NorenWClientTP",
            websocket='wss://profitmax.profitmart.in/NorenWSTP/',
        )

        ret = api.login(
            userid=self.uid,
            password=self.pwd,
            twoFA=self.factor2,
            vendor_code=self.vc,
            api_secret=self.app_key,
            imei="1234"
        )
        if ret is not None:
            logging.info("Noren object created successfully!!")
            Controller.norenLogin = api
            Controller.brokerLogin = api

    def getBrokerLogin(self):
        return Controller.brokerLogin

    def getBrokerName(self):
        return Controller.brokerName
