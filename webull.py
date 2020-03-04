import json
import requests
import uuid
import hashlib
import time

class webull :
    def __init__(self) :
        self.session = requests.session()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
        }
        # self.auth_method = self.login_prompt
        self.access_token = ''
        self.account_id = ''
        self.refresh_token = ''
        self.trade_token = ''
        self.uuid = ''
        self.did = '1bc0f666c4614a11808a372f14ffe42c'

    '''
    for login purposes password need to be hashed password, figuring out what hash function is used currently.
    '''
    def login(self, username='', password='') :
        # with webull md5 hash salted
        password = ('wl_app-a&b@!423^' + password).encode('utf-8')
        md5_hash = hashlib.md5(password)
        # password = md5_hash.hexdigest()
        data = {'account': username,
                'accountType': 2,
                'deviceId': self.did,
                'pwd': md5_hash.hexdigest(),
                'regionId': 1}
        response = requests.post('https://userapi.webull.com/api/passport/login/account', json=data, headers=self.headers)

        result = response.json()
        if result['success'] == True and result['code'] == '200' :
            self.access_token = result['data']['accessToken']
            self.refresh_token = result['data']['refreshToken']
            self.token_expire = result['data']['tokenExpireTime']
            self.uuid = result['data']['uuid']
            return True
        else :
            return False

    def refresh_login(self) :
        # password = md5_hash.hexdigest()
        headers = self.headers
        headers['did'] = self.did
        headers['access_token'] = self.access_token

        data = {'refreshToken': self.refresh_token}

        response = requests.post('https://userapi.webull.com/api/passport/refreshToken?refreshToken=' + self.refresh_token, json=data, headers=headers)

        result = response.json()
        if 'accessToken' in result and result['accessToken'] != '' and result['refreshToken'] != '' and result['tokenExpireTime'] != '' :
            self.access_token = result['accessToken']
            self.refresh_token = result['refreshToken']
            self.token_expire = result['tokenExpireTime']
            return True
        else :
            return False


    '''
    get some contact details of your account name, email/phone, region, avatar...etc
    '''
    def get_detail(self) :
        headers = self.headers
        headers['did'] = self.did
        headers['access_token'] = self.access_token

        response = requests.get('https://userapi.webull.com/api/user', headers=headers)
        result = response.json()

        return result

    '''
    get account id
    call account id before trade actions
    '''
    def get_account_id(self) :
        headers = self.headers
        headers['did'] = self.did
        headers['access_token'] = self.access_token

        response = requests.get('https://tradeapi.webulltrade.com/api/trade/account/getSecAccountList/v4', headers=headers)
        result = response.json()

        if result['success'] == True :
            self.account_id = str(result['data'][0]['secAccountId'])
            return True
        else :
            return False

    '''
    get important details of account, positions, portfolio stance...etc
    '''
    def get_account(self) :
        headers = self.headers
        headers['did'] = self.did
        headers['access_token'] = self.access_token

        response = requests.get('https://tradeapi.webulltrade.com/api/trade/v2/home/' + self.account_id , headers=headers)
        result = response.json()

        return result

    '''
    output standing positions of stocks
    '''
    def get_positions(self) :
        data = self.get_account()

        return data['positions']

    '''
    output numbers of portfolio
    '''
    def get_portfolio(self) :
        data = self.get_account()

        output = {}
        for item in data['accountMembers'] :
            output[item['key']] = item['value']

        return output

    '''
    get open orders
    '''
    def get_orders(self) :
        data = self.get_account()

        # output = {}
        # for item in  :
        #     output[item['key']] = item['value']

        return data['openOrders']

    '''
    authorize trade, must be done before trade action
    '''
    def get_trade_token(self, password='') :
        headers = self.headers
        headers['did'] = self.did
        headers['access_token'] = self.access_token

        # with webull md5 hash salted
        password = ('wl_app-a&b@!423^' + password).encode('utf-8')
        md5_hash = hashlib.md5(password)
        # password = md5_hash.hexdigest()
        data = {'pwd': md5_hash.hexdigest()}

        response = requests.post('https://tradeapi.webulltrade.com/api/trade/login', json=data, headers=headers)
        result = response.json()

        if result['success'] == True :
            self.trade_token = result['data']['tradeToken']
            return True
        else :
            return False

    '''
    lookup ticker_id
    '''
    def get_ticker(self, stock='') :
         response = requests.get('https://infoapi.webull.com/api/search/tickers5?keys=' + stock + '&queryNumber=1')
         result = response.json()

         ticker_id = 0
         if len(result['list']) == 1 :
             for item in result['list'] :
                 ticker_id = item['tickerId']
         return ticker_id

    '''
    ordering
    '''
    def place_order(self, stock='', price='', quant=0) :

         headers = self.headers
         headers['did'] = self.did
         headers['access_token'] = self.access_token
         headers['t_token'] = self.trade_token
         headers['t_time'] = str(round(time.time() * 1000))

         data = {'action': 'BUY', #  BUY or SELL
                 'lmtPrice': float(price),
                 'orderType': 'LMT', # "LMT","MKT","STP","STP LMT"
                 'outsideRegularTradingHour': True,
                 'quantity': int(quant),
                 'serialId': str(uuid.uuid4()), #'f9ce2e53-31e2-4590-8d0d-f7266f2b5b4f'
                 'tickerId': self.get_ticker(stock),
                 'timeInForce': 'GTC'} # GTC or DAY or IOC

         response = requests.post('https://tradeapi.webulltrade.com/api/trade/order/' + self.account_id + '/placeStockOrder', json=data, headers=headers)
         result = response.json()

         if result['success'] == True :
             return True
         else :
             return False

    '''
    retract an order
    '''
    def cancel_order(self, order_id='') :

        headers = self.headers
        headers['did'] = self.did
        headers['access_token'] = self.access_token
        headers['t_token'] = self.trade_token
        headers['t_time'] = str(round(time.time() * 1000))

        data = {}

        response = requests.post('https://tradeapi.webulltrade.com/api/trade/order/' + self.account_id + '/cancelStockOrder/' + str(order_id) + '/' + str(uuid.uuid4()), json=data, headers=headers)
        result = response.json()

        if result['success'] == True :
            return True
        else :
            return False

    '''
    get price quote
    '''
    def get_quote(self, stock='') :
        response = requests.get('https://quoteapi.webull.com/api/quote/tickerRealTimes/v5/' + str(self.get_ticker(stock)))
        result = response.json()

        return result

if __name__ == '__main__' :
    webull = webull()
    webull.login('luckhoi89@gmail.com', 'Khangluc1.')
    webull.get_account_id()
    webull.get_trade_token('127199')
    'print(webull.get_account())'
    
    #get the price of the sticker you want
    print(webull.get_quote('cost')['close'])