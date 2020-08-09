import requests
import json


def ReadKey(filename):
    '''
    从文件中获取当前使用的 key
    :param filename:
    :return:
    '''
    try:
        with open(filename, 'r', encoding='utf-8') as f_key:
            content = f_key.readlines()
    except FileNotFoundError:
        raise Exception('Key File not exists, Please create key file first.')
    return content[0]


def GenerateRequestAddress(BaseUrl, ParameterDict, ConnChar='&'):
    '''
    根据api文档生成查询所需URL
    :param BaseUrl:
    :param ParameterDict:
    :param ConnChar:
    :return:
    '''

    result = ConnChar.join(str(key) + '=' + str(value) for key, value in ParameterDict.items())
    result = BaseUrl + result
    return result


def GetResponse(Url, timeout=30):
    '''
    使用requests 包获取当前Url的返回值。
    :param Url:
    :param timeout:
    :return:
    '''
    try:
        r = requests.get(url=Url, timeout=timeout)
        if r.status_code == 200:
            return r.text
        else:  # Todo: Retry.
            return None
    except Exception as e:
        print('Error in Requesting, Error: {}'.format(e))
        return None


def ParseJson(JsonContent):
    '''
    字符串解析成字典类型
    :param JsonContent:
    :return:
    '''
    return json.loads(JsonContent)


def CalDistance(OriginLocation, DstLocation):
    x1, y1 = OriginLocation.split(',')
    x2, y2 = DstLocation.split(',')
    x1 = float(x1)
    x2 = float(x2)
    y1 = float(y1)
    y2 = float(y2)
    return (x1 - x2) ** 2 + (y1 - y2) ** 2


def RemoveDictKey(InputDict, RemoveKey='id'):
    '''
    去除地点dict中不需要的id键值
    :param InputDict:
    :param RemoveKey:
    :return:
    '''
    del InputDict[RemoveKey]
    return InputDict
