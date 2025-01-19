import datetime as dt
import requests, os, subprocess, json
#Tips: argparse - process arguments from commands
import argparse, configparser

#Py: for covert querystring into json 
from urllib.parse import parse_qs
from CallHelper import ApiCopyTradeCallHelper

def api_command_call(api_url, http_method, api_key, api_secret, mode=0, payload_parameters:dict = None, payload_message:str = None) -> str:
    """
    Call API with system command
    
    :param api_url: API的URL
    :param http_method: API HTTP METHOD ('GET','POST' ...)
    :param api_key: API Public key
    :param api_secret: API Secret key
    :param payload_parameters: API Payload with json format
    :param payload_message: API Payload with query string (parameters) format
    :return Command 執行結果

    Command Sample:
    echo -n "symbol=BTCETH&side=BUY&type=MARKET&quantity=0.001&recvWindow=60000&timestamp=1729852860000” 
    openssl dgst -sha256 -hmac "4OSPBpbGltHB1rHDTFr44bigAOgEktJcdeE72jrsViiEHaZmzVNNlo0b01AdRA7x" 
    -> 7c39f2b0dcb194dabf0687088e14552c4edf126f9503f8a5d096d95508707014
    """
    request_command = None
    request_url = api_url

    # 如果是 GET method 且 沒有帶任何 payload, 此時當作不需要簽章處理. api url 即是 request url
    if (http_method.upper() == 'GET' and (not payload_parameters) and not (payload_message)):
        request_command = f'curl -X {http_method} "{request_url}"'
    else : 
        payload_str = ""
        if payload_message : payload_str = payload_message
        elif payload_parameters and ('timestamp' not in payload_parameters) : 
            payload_parameters['timestamp'] = ApiCopyTradeCallHelper.get_api_trade_timestamp() 
            payload_str = ApiCopyTradeCallHelper.get_payload(payload_parameters)
        signature = ApiCopyTradeCallHelper.generate_signature(api_key, api_secret, payload_str) if payload_str else None
    
        payload = payload_str + "&signature=" + signature if signature else payload_str
        request_url = f'{api_url}?{payload}' if payload else f'{api_url}'
        request_command = f'curl -H "X-MBX-APIKEY:{api_key}" -X {http_method} "{request_url}"'
        #Tips: os.system(command) can just execute command, but no output return python
        # os.system(req_command)

    response = None
    if mode == 1 : return request_command
    try:
        print("!!Executed Curl Command: \n  %s"%request_command)
        # Tips: subprocess.check_output 可將 os command 執行結果 回傳 python 作為字串(text=True)
        response = subprocess.check_output(request_command, shell=True, text=True)
        # Tips: 在任何 f-string 中，{var_name}, {expression}, {function_name(...)} 作为变量和表达式的占位符，并在运行时被替换成相应的值。
        # print(f"\nResponse = {response}")
    except subprocess.CalledProcessError as e:
        print(f'\nOperation Error : executing command Fail: {e}')
    
    return response

def api_restful_call(api_url, http_method, api_key, api_secret, payload_parameters:dict = None, payload_message:str = None): 
    """
    Call API with Restful Request
    
    :param api_url: API的URL
    :param http_method: API HTTP METHOD ('GET','POST' ...)
    :param api_key: API Public key
    :param api_secret: API Secret key
    :param payload_parameters: API Payload with json format
    :param payload_message: API Payload with query string (parameters) format
    :return Command 執行結果
    """
    request_headers = {"X-MBX-APIKEY" : api_key} if api_key else None

    # 如果是 GET method 且 沒有帶任何 payload, 此時當作不需要簽章處理. api url 即是 request url
    if (http_method.upper() == 'GET' and (not payload_parameters) and not (payload_message)) : 
        return ApiCopyTradeCallHelper.api_trade_call(api_url, http_method, request_headers, payload_parameters)

    if payload_parameters : 
        if "timestamp" not in payload_parameters.keys(): 
            payload_parameters['timestamp'] = ApiCopyTradeCallHelper.get_api_trade_timestamp()
    payload_str = payload_message if payload_message else ApiCopyTradeCallHelper.get_payload(payload_parameters)
    # print("Original Payload String: \n  %s"%payload_str)

    if payload_str == payload_message : 
        if (payload_str.find("signature") < 0):
            payload_str = payload_message + "&timestamp=" + ApiCopyTradeCallHelper.get_api_trade_timestamp() \
                if (payload_message.find("timestamp") < 0) else payload_message
            
            signature = ApiCopyTradeCallHelper.generate_signature(api_key, api_secret, payload_str)
            payload_str = payload_str + "&signature=" + signature
            print("Restful payload message: \n  %s"%payload_str)
            payload_dict = { k: str(v).strip().strip('\'[]') for k,v in parse_qs(payload_str).items()}
            payload_with_signature_str = json.dumps(payload_dict)
            payload_parameters = json.loads(payload_with_signature_str)
        else: payload_parameters = json.loads(payload_str)

    else : 
        if "signature" not in payload_parameters.keys():
            signature = ApiCopyTradeCallHelper.generate_signature(api_key, api_secret, payload_str) if (api_key and api_secret) else None
        if signature : payload_parameters['signature'] = signature

    print("Restful payload parameters: \n  %s"%payload_parameters)
    response = ApiCopyTradeCallHelper.api_trade_call(api_url, http_method, request_headers, payload_parameters)

    return response

if __name__ == '__main__':

    guide = "\n需要簽章的 API 直接從command 指定參數時,至少需同時指定 url, method, key, secret, payload 等 api 呼叫時所需基本參數方是有效的執行指令;\n" + \
        "若要從ini讀取 api 相關參數, 則需要 -f 指定 ini 檔案名稱(相對或完整路徑) 及 -t tag名稱(預設是 default 時不必指定);\n" + \
        "也可 -f 搭配其他參數一起使用, 而指令中如有與檔案讀取到的 api 參數值衝突, 指令的參數值將被採用.\n" + \
        "For Example:\n" + \
        "  1. python main.py -f apikey.ini ; (curl command mode)\n" + \
        "  2. python main.py -f apikey.ini -t test ;\n" + \
        "  3. python main.py -u 'https://api.binance.com/api/v1/order' -m post -k YJXM6xV4boqmecCUVClLHjA3USoLBgEow7vzRLxrGYKGG3zi5mGWYpD3aH9YnB9O\n " + \
        "        -s YGUCnWzoEkSQKJQl5CXftQyVI0MTdhtQp1RgN45na9XeR20J5EM3A9K96IXxHcgH\n" + \
        '         -p "{\'symbol\': \'BTCUSDT\', \'positionSide\': \'BOTH\', \'side\': \'BUY\', \'type\': \'MARKET\', \'quantity\': 0.002}"\n' + \
        "  4. python main.py -f apikey.ini -t buybtc -u \"https://api.binance.com/api/v1/order\" \n" + \
        "  5. python main.py -f apikey.ini -t buybtc -msg \"symbol=BNBUSDT&side=SELL&type=MARKET&quantity=1&timstamp=1730365248000\" -tsd 2\n" + \
        "  6. python main.py -f apikey.ini -t test -e 1 (api restful mode)\n" + \
        "  7. python main.py -f apikey.ini -t test -e 2 -tsd 10  (Not Executed mode, return curl command)\n" \
        "  8. python main.py -f apikey.ini -m get -u https://api.binance.com/api/v3/exchangeInfo?symbol=BNBUSDT (For Get API, url must be completed if contains query parameters) \n" 
    
    parser = argparse.ArgumentParser(description="Running Binance Copy Trading With API KEY", usage=guide)
    
    parser.add_argument('-u', '--url', required=False, help="API 請求資源路徑 URL, eg. https://api.binance.com/fapi/v3/order")
    parser.add_argument('-m', '--method', required=False, help="API http method, GET|POST ...")
    parser.add_argument('-k', '--key', required=False, help="binance api key")
    parser.add_argument('-s' ,'--secret', required=False, help="binance api secret key")
    parser.add_argument('-p' ,'--params', required=False, help="Payload Parameters")
    parser.add_argument('-msg' ,'--message', required=False, help="Payload Parameters with query string format")
    parser.add_argument('-tsd' ,'--timestampdiff', type=int, required=False, help="產生的 TimeStamp 時間 與現在相差的秒數")
    parser.add_argument('-f' ,'--file', required=False, help="api key ini file")
    parser.add_argument('-t' ,'--tag', required=False, default="default", help="the tag in the ini file")
    parser.add_argument('-e', '--execute', type=int, required=False, default=0, help="execute mode, 0: curl command call(default), 1: restful call, 2: get curl command")
    #Tips: parser.print_help() can review the arguments help results
    # parser.print_help()
    args = parser.parse_args()

    api_url, http_method, api_key, api_secret, tsd, file, tag = args.url, args.method, args.key, args.secret, args.timestampdiff, args.file, args.tag
    payload_parameters = None
    payload_message = args.message
    if args.file: 
        # Return Tuple: ini_url, ini_method, ini_api_key, ini_secret, ini_parameters
        ini_tag = ApiCopyTradeCallHelper.parse_api_ini(file, tag)
        api_url, http_method, api_key, api_secret, payload_parameters = ini_tag[0], ini_tag[1], ini_tag[2], ini_tag[3], ini_tag[4]
    #1 Tips: 如果輸入 file 參數 又同時指定一些 參數跟  file 內 的參數值衝突, 以輸入的參數取代 file 內的參數值
    if args.url : api_url = args.url
    if args.method : http_method = args.method.upper()
    if args.key : api_key = args.key
    if args.secret : api_secret = args.secret
    # 如果 用戶在指令中指定了 payload parameters 則 ini 的 parameters 失效
    if args.params : payload_parameters = args.params
    # 如果 用戶在指令中指定了 payload message , 則 payload parameters 失效, 以 payload message 為 payload 
    if args.message : payload_parameters = None
    #1 End

    #2 Tips: 如果指令中 指定了 timestamp diff , 則 payload 中的 timestamp 會被取代
    if tsd and payload_parameters: payload_parameters["timestamp"] = ApiCopyTradeCallHelper.get_api_trade_timestamp(tsd)
    if tsd and payload_message: 
        if (payload_message.find("timestamp") >= 0) : 
            #3 Remove original timestamp
            ts_start = payload_message.find("&timestamp=")
            ts_end = ts_start + len("&timestamp=") + 13
            ts_str = payload_message[ts_start:ts_end]
            payload_message = payload_message.replace(ts_str,"")
            #3
        payload_message = payload_message + "&timestamp=" + ApiCopyTradeCallHelper.get_api_trade_timestamp(tsd)
        #print("payload_message with tsd: %s"%payload_message)
    #2 End
    
    if args.execute == 0:
        response = api_command_call(api_url, http_method, api_key, api_secret, 0, payload_parameters, payload_message)
        print(f"\n!!CURL Response : \n  {response}\n")
    elif args.execute == 1:
        response = api_restful_call(api_url, http_method, api_key, api_secret, payload_parameters, payload_message)
        print(f"\n!!Restful Response : \n  {response}\n")
    else:
        response = api_command_call(api_url, http_method, api_key, api_secret, 1, payload_parameters, payload_message)
        print(f"\n!! Curl Command : \n  {response}\n")






