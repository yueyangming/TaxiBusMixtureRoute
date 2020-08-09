# Powered by Harold Yue
# Date: 2020.8.8

from Common import *
import time


def GetLocation(Address, City, key, BaseUrl='https://restapi.amap.com/v3/geocode/geo?'):
    '''
    通过地理位置api得到当前地址的location 字符串， 注意：当前只取了返回的第一个地址。
    :param Address:
    :param key:
    :param BaseUrl:
    :return:
    '''
    ParameterDict = {
        'address': Address,
        'city': City,
        'key': key,
        'output': 'JSON'
    }
    url = GenerateRequestAddress(BaseUrl, ParameterDict)
    response = GetResponse(url)
    ResultDict = ParseJson(response)

    try:
        tmp_geocodes = ResultDict['geocodes']
        result = tmp_geocodes[0]['location']
        return result
    except Exception as e:
        print('Error in parsing dict, Error: {}'.format(e))
        return None


def ParseSegmentBusline(SegmentDict):
    '''
    解析当前分段Dict， 得到 当前地铁线路，起点地铁站，终点地铁站。目前只考虑了地铁的情况。
    :param SegmentDict:
    :return:
    '''
    if SegmentDict['type'] != '地铁线路':
        return None
    MetroLine = SegmentDict['name']
    DepStop = SegmentDict['departure_stop']['name']
    DstStop = SegmentDict['arrival_stop']['name']
    result = (MetroLine, DepStop, DstStop)
    return result


def GetBusRouteDict(OriginLocation, DstLocation, City, key,
                    BusRouteBaseUrl='https://restapi.amap.com/v3/direction/transit/integrated?'):
    TempleteBusParameterDict = {
        'strategy': 0,
        'key': key,
        'nightflag': 0,
        'date': '2020-8-8',
        'time': '11:00'
    }
    BusRouteParameterDict = TempleteBusParameterDict.copy()
    BusRouteParameterDict['origin'] = OriginLocation
    BusRouteParameterDict['destination'] = DstLocation
    BusRouteParameterDict['city'] = City
    BusRouteParameterDict['cityd'] = City
    BusRouteUrl = GenerateRequestAddress(BusRouteBaseUrl, BusRouteParameterDict)
    BusJson = GetResponse(BusRouteUrl)
    BusRouteDict = ParseJson(BusJson)
    return BusRouteDict


def GetBaseBusInfo(BusRouteDict):
    '''
    获取当前公交规划路线的基本信息，总耗时，步行距离和换乘次数。
    :param BusRouteDict:
    :return:
    '''
    BestTransit = BusRouteDict['route']['transits'][0]  # 假定第一个得到的路线为最优路线。

    BaseDuration = int(float(BestTransit['duration']) / 60)  # 默认为秒，转化为分钟
    BaseWalkingDistance = float(BestTransit['walking_distance']) / 1000  # 默认为米，转化为千米

    TransferTimes = 0
    for EachSegment in BestTransit['segments']:
        if len(EachSegment['bus']['buslines']) > 0:
            TransferTimes += 1

    return BaseDuration, BaseWalkingDistance, TransferTimes


def GetBusLinesInCurrentTransit(BusRouteDict):
    '''
    获取当前规划的所有路径中所有的地铁线路
    :param BusRouteDict:
    :return:
    '''
    result = []

    for CurrentTransit in BusRouteDict['route']['transits']:
        for CurrentSegment in CurrentTransit['segments']:
            try:
                BusLineSegmentDict = CurrentSegment['bus']['buslines'][0]
                if BusLineSegmentDict['type'] != '地铁线路':
                    continue

            except IndexError as e:
                continue
            TmpResult = ParseSegmentBusline(BusLineSegmentDict)  # 当前线路名，起点，终点站
            if TmpResult is not None:
                CurrentBusLine, _, _ = TmpResult
                result.append(CurrentBusLine)
    result = list(set(result))
    return result


def GetBusLineStops(BusLineString, City, key,
                    BusLineJsonFilename='BusLinesStops.json'):
    '''
    从上一步中地铁线的线路名获取当前地铁线路的沿线站点名及Location
    已知Bug，在解析13号线的过程中出现问题， 经过测试发现是 api不能很好的得到 13号线沿线地铁站的Location，如解析张江路会解析到静安区地铁站等
    :param BusLineString:
    :return: list of dict.
    Example: [{'name': '滴水湖', 'id': '310100024526002', 'location': '121.929583,30.907245'}, {'name': '龙阳路', 'id': '310100024526014', 'location': '121.557848,31.201988'}]
    '''
    result = []
    BusLineName = BusLineString.split('(')[0]
    # Read json file
    try:
        with open(BusLineJsonFilename, 'r', encoding='utf-8') as f_BusLineStops:
            BusLineStopsDict = json.load(f_BusLineStops)
    except Exception as e:
        print('Error in Reading BusLine json file. Error : {}'.format(e))
        BusLineStopsDict = {}
    if BusLineName in BusLineStopsDict.keys():  # 之前访问过，已经被离线存储
        return BusLineStopsDict[BusLineName]
    else:

        DepStop, DstStop = BusLineString.split('(')[1].split(')')[0].split('--')
        # '地铁16号线(滴水湖--龙阳路)' -> ('滴水湖'， '龙阳路'）  Todo 此处用正则会更好一些
        DepStop = DepStop + '地铁站'
        DstStop = DstStop + '地铁站'
        OriginLocation = GetLocation(DepStop, City, key)
        DstLocation = GetLocation(DstStop, City, key)
        CurrentBusLineDict = GetBusRouteDict(OriginLocation, DstLocation, City, key)

        Segments = CurrentBusLineDict['route']['transits'][0]['segments']  # 假设认为第一个路线为直达路线（一般情况下都有效有效）
        for EachSegment in Segments:
            CurrentBusLines = EachSegment['bus']['buslines']
            if len(CurrentBusLines) == 0:  # No bus stop information.
                continue

            result.append(RemoveDictKey(CurrentBusLines[0]['departure_stop'], 'id'))  # 加入起点
            ViaStopList = CurrentBusLines[0]['via_stops']
            for EachViaStop in ViaStopList:  # 加入每一个经停站
                result.append(RemoveDictKey(EachViaStop))

            result.append(RemoveDictKey(CurrentBusLines[0]['arrival_stop']))  # 加入终点
        # 把新的结果储存进json文件
        BusLineStopsDict[BusLineName] = result
        with open(BusLineJsonFilename, 'w', encoding='utf-8') as f_BusLineStops:
            json.dump(BusLineStopsDict, f_BusLineStops)
        return result


def GetDriveRouteDict(OriginLocation, DstLocation, UserKey,
                      DriveRouteBaseUrl = 'https://restapi.amap.com/v3/direction/driving?parameters'):
    '''
    获取驾车路线规划返回dict
    :param OriginLocation:
    :param DstLocation:
    :param UserKey:
    :param DriveRouteBaseUrl:
    :return:
    '''
    DriveParameterDict = {'strategy': 0, 'extensions': 'all',
                          'key': UserKey,
                          'origin': OriginLocation,
                          'destination': DstLocation}
    DriveRouteUrl = GenerateRequestAddress(DriveRouteBaseUrl, DriveParameterDict)
    DriveRouteJson = GetResponse(DriveRouteUrl)
    DriveRouteDict = ParseJson(DriveRouteJson)
    return DriveRouteDict


def ParseDriveRouteDict(DriveRouteDict):
    '''
    解析DriverRouteDict， 得到三个想要的数据， 两地之间驾车距离Distance，耗时Duration和打车费用TaxiCost
    :param DriveRouteDict:
    :return:
    '''
    Distance = float(DriveRouteDict['route']['paths'][0]['distance']) / 1000  # 默认为米，转化为千米
    Duration = float(DriveRouteDict['route']['paths'][0]['duration']) / 60  # 默认为秒，转化为分钟
    TaxiCost = int(float(DriveRouteDict['route']['taxi_cost']))
    return Distance, Duration, TaxiCost


def CostFunction(BaseDuration, BaseWalkingDistance, BaseTransferTimes,
                 CurrentPlanDuration, CurrentPlanWalkingDistance, CurrentPlanTransferTimes, WeightDict=None):
    '''
    计算当前计划的收益。
    :param BaseDuration:
    :param BaseWalkingDistance:
    :param BaseTransferTimes:
    :param CurrentPlanDuration:
    :param CurrentPlanWalkingDistance:
    :param CurrentPlanTransferTimes:
    :param WeightDict:
    :return:
    '''
    if WeightDict is None:
        WeightDict = {
            'TransferWeight': 5,
            'WalkingWeight': 5,
            'DurationWeight': 0.5
        }
    result = WeightDict['DurationWeight'] * (BaseDuration - CurrentPlanDuration) + \
             WeightDict['WalkingWeight'] * (BaseWalkingDistance - CurrentPlanWalkingDistance) + \
             WeightDict['TransferWeight'] * (BaseTransferTimes - CurrentPlanTransferTimes)
    return int(result)


if __name__ == '__main__':

    ### 用户自定义参数区域。
    OriginAddress = '上海高等研究院'  # 起点地址
    DstAddress = '世纪大道(地铁站)'  # 终点地址
    City = '上海'
    # Cost function weight dict.
    WeightDict = {
        'TransferWeight': 5,  # 为了节省一次换乘愿意付出多少银子？
        'WalkingWeight': 5,  # 为了节省一公里步行距离愿意付出多少银子？
        'DurationWeight': 0.5  # 为了节省一分钟时间愿意付出多少银子？
    }
    ### 用户定义参数区域结束。
    KeyFilename = 'UserInfo.inf'
    BusLineJsonFilename = 'BusLinesStops.json'

    # BaseUrl = 'https://restapi.amap.com/v3/geocode/geo?'
    BusRouteBaseUrl = 'https://restapi.amap.com/v3/direction/transit/integrated?'

    UserKey = ReadKey(KeyFilename)
    key = UserKey

    StartTime = time.time()

    # 第一步，获取起点和终点的 Location坐标。从地址转化为 Location
    OriginLocation = GetLocation(OriginAddress, City, UserKey)
    DstLocation = GetLocation(DstAddress, City, UserKey)

    # 第二步，获取默认公交规划（并以此作为当前的最优解）中的路线(和站点)，总时长，步行距离，以及换乘次数。
    BusRouteDict = GetBusRouteDict(OriginLocation, DstLocation, City, key,
                                   BusRouteBaseUrl)
    # 获取总耗时，步行距离，以及换乘次数。
    BaseDuration, BaseWalkingDistance, BaseTransferTimes = GetBaseBusInfo(BusRouteDict)

    # 获取当前所有规划路线中出现的地铁线路
    BusRouteList = GetBusLinesInCurrentTransit(BusRouteDict)
    # 输出形如 ： ['地铁13号线(张江路--金运路)', '地铁16号线(滴水湖--龙阳路)', '地铁2号线(浦东国际机场--徐泾东)']
    # Bug: 13号线沿线的地铁站api识别有问题。 Update: 已通过替代方案已经在Json文件中更新现有的站点列表。
    # 第三步， 列出所有可能的地铁站
    '''
    在这里有一个迭代的过程。 上一步已经得到了相关的地铁线路和起点终点
    这里做一个假设，即 从起点到终点的最优公交规划路线恰好为从起点到终点沿当前地铁线路一口气做到底的路线。
    则，如果想获取一条地铁线路中所有的站点名称，可以通过一次公交规划查询，第一个查询结果后所有经停站。
    '''
    AllStopList = []
    for CurrentBusLineString in BusRouteList:
        CurrentBusLineStopsList = GetBusLineStops(CurrentBusLineString, City, UserKey, BusLineJsonFilename)
        AllStopList += CurrentBusLineStopsList

    # 初筛， 去重， 减去离起点过远的地铁站。 此处的threshold为起点到终点的距离
    ThresholdDistance = CalDistance(OriginLocation, DstLocation) * 2 / 3
    VisitedNames = []
    UniqueStopList = []
    for EachStop in AllStopList:
        if EachStop['name'] not in VisitedNames:
            VisitedNames.append(EachStop['name'])
            if CalDistance(EachStop['location'], OriginLocation) < ThresholdDistance:
                UniqueStopList.append(EachStop)
    # 第四步，开始进行搜索，和cost function的判断
    # 拆成子任务，
    # 4a. 当前地铁站Location
    BestBenefit = 0
    BestPlan = {}
    for CurrentStop in UniqueStopList:
        CurrentStopLocation = CurrentStop['location']

        # 4b. 起点到当前地铁站的 驾车距离规划。
        # Stage 1: Drive to Metro Stop.
        DriveRouteDict = GetDriveRouteDict(OriginLocation=OriginLocation,
                                           DstLocation=CurrentStopLocation,
                                           UserKey=UserKey)
        DriveDistance, DriveDuration, TaxiCost = ParseDriveRouteDict(DriveRouteDict)
        # Stage 2: Metro to DstLocation. # 4c. 当前地铁站到终点的公交路线规划。 返回时间，换乘次数
        CurrentBusRouteDict = GetBusRouteDict(CurrentStopLocation, DstLocation, City, key)
        CurrentBusDuration, CurrentBusWalkingDistance, CurrentBusTransferTimes = GetBaseBusInfo(CurrentBusRouteDict)

        CurrentPlanDuration = DriveDuration + CurrentBusDuration
        # 4d. 计算cost function
        CurrentPlanCostFunction = CostFunction(BaseDuration, BaseWalkingDistance, BaseTransferTimes,
                                               CurrentPlanDuration, CurrentBusWalkingDistance, CurrentBusTransferTimes)

        if CurrentPlanCostFunction > TaxiCost:
            CurrentBenefit = CurrentPlanCostFunction - TaxiCost
            if CurrentBenefit > BestBenefit:  # Update Best benefit
                BestBenefit = CurrentBenefit
                BestPlan = {'StopName': CurrentStop['name'],
                            'Duration': CurrentPlanDuration,
                            'WalkingDistance': CurrentBusWalkingDistance,
                            'TaxiCost': TaxiCost,
                            'Benefit': CurrentBenefit,
                            'CostFunction': CurrentPlanCostFunction}

    # 最后的输出。 如果找到了更好的方案
    if BestBenefit > 0:
        print('从{} 到 {}'.format(OriginAddress, DstAddress))
        print('新计划， 打车到 {}地铁站，花费 {}， 效用{}'.format(BestPlan['StopName'], BestPlan['TaxiCost'], BestPlan['Benefit']))
        print('总共耗时对比： 旧： {}min, 新 : {}min'.format(BaseDuration, BestPlan['Duration']))
        print('总步行距离对比: 旧 ： {}千米, 新： {}千米'.format(BaseWalkingDistance, BestPlan['WalkingDistance']))
        # print('From {} To {}. \n Best Plan: Take Taxi to {}, Cost : {}, Benefit: {}.\n '.format(OriginAddress, DstAddress,
        #                                                                                         BestPlan['StopName'],
        #                                                                                         BestPlan['TaxiCost'],
        #                                                                                         BestPlan['Benefit']) +
        #       'Old Plan Duration: {}min, New Plan Duration: {}min \n '.format(BaseDuration, BestPlan['Duration']) +
        #       'Old Plan Walking Distance: {}km, New Plan Walking Distance: {}km. '.format(BaseWalkingDistance, BestPlan['WalkingDistance']))
    else:
        print('No better solution for current route.')
    EndTime = time.time()
    # print('Running time : {}s, searched {} Metro stations'.format(EndTime - StartTime, len(UniqueStopList)))
    print('程序运行时间： {}s， 共搜索 {}个地铁站'.format(EndTime - StartTime, len(UniqueStopList)))
