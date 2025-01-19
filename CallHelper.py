# tips: configparse - process ini config files
import os, json, hmac, hashlib, requests, configparser
import datetime as dt

class ApiCopyTradeCallHelper:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret

    # Tips: @staticmethod 修飾子 指定 function 為 靜態函式
    @staticmethod
    # Tips: function_parameter_name:int 指定 參數為 整數 型態
    # Tips: function_name() -> str : 指定回傳 字串
    def get_api_trade_timestamp(second_diff:int = 1) -> str :
        """
        產生 binance api call 的 13 碼 timestamp 整數字串.

        :param second_diff: 要產生的 TimeStamp 的時間 多餘 當前時間的秒數, 預設是 1 秒
        :return 一個 13 位 的 TimeStamp 整數字串, 其時間是 呼叫 函式的當下 加上 second_diff 秒 後產生的 TimeStamp
        """
        
        now = dt.datetime.now()
        ts = int(round(dt.datetime.timestamp(now+dt.timedelta(seconds = second_diff))))*1000
        return str(ts)

    @staticmethod
    def api_trade_call(request_url, api_method, api_headers, api_data):
        """
        調用RESTful API的通用函式

        :param request_url: API的URL
        :param action: API Call , Example: FUT_ORDER, SPOT_ORDER , 要調用的 API 的代表字
        :param api_headers: HTTP標頭(字典)
        :param api_data: 表單數據（字典）
        :return API回應的內容
        """

        print("Request URL : %s"%request_url)

        try:
            #Tips: data is payload/body
            match api_method.upper():
                case "GET": response = requests.get(request_url, headers=api_headers, data=api_data)
                case "POST": response = requests.post(request_url, headers=api_headers, data=api_data)
                case _: response = requests.request(url=request_url, method=api_method, headers=api_headers, data=api_data)
            # 檢查回應狀態碼
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f' API HTTP ERROR: {http_err}')
            return None
        except Exception as err:
            print(f'API ERROR: {err}')

    @staticmethod
    def parse_api_ini(file, tag): 
        # 創建 configparser 物件
        ini_config = configparser.ConfigParser()
        # 讀取配置文件
        ini_config.read(file, encoding='utf-8')
        if not tag: tag = "default"

        if ini_config.has_section(tag):
            try:
                # 獲取 Section1 中的 Key1 和 Key2 的值
                ini_url = ini_config[tag]['url']
                ini_method = ini_config[tag].get('method').upper()
                ini_api_key = ini_config[tag].get('api_key')
                ini_secret = ini_config[tag].get('api_secret')
                ini_parameters = json.loads(ini_config[tag]['parameters']) if ini_config[tag].get('api_secret') else None

                print("ini:\n\turl={}\n\tmethod={}\n\tapi_key={}\n\tapi_secret={}\n\tparameter={}\n".format(ini_url,ini_method,ini_api_key,ini_secret, ini_parameters))
        
                return ini_url, ini_method, ini_api_key, ini_secret, ini_parameters
            except KeyError as ke:
                print(f'\nOperation Error : executing command - read ini Fail -> {ke}')
            except ValueError as ve:
                print(f'\nOperation Error : executing command - value error -> {ve}')
        else : 
            tag_error = f"Operation Error : executing command - value error -> the '{tag}' section is not found."
            raise Exception(tag_error)

    @staticmethod
    def get_payload(params=None) -> str :
        """ 
        產生 API Request 的 完整 Query String 型式的 Payload

        :param params: dict 型態的 payload parameters
        :return Query String 型式的 Payload
        """

        payload_init = '&'.join([f'{param}={value}' for param, value in params.items()]) if params else None
        return payload_init
    
    @staticmethod
    def generate_signature(api_key, api_secret, payload) -> str:
        """
        生成基於SHA256的HMAC簽名
        
        :param api_key: API Key
        :param api_secret: API Secret
        :param payload: 要簽名的 Payload, 使用 querystring 型式 - Example, p1=v1&p2=v2&p3=v3
        :return: HMAC簽名
        """

        # 將API Secret轉換為字節
        secret_bytes = api_secret.encode('utf-8')
        # 創建HMAC對象
        hmac_obj = hmac.new(secret_bytes, payload.encode('utf-8'), hashlib.sha256)
        # 生成簽名
        signature = hmac_obj.hexdigest()
        return signature
