这个程序的功能是，尝试做一个从起点到终点的 公交+打车的混合路线规划。具体的一些思想和实现思路可以在知乎回答这里看到： https://www.zhihu.com/question/51314788/answer/1394812871

使用说明：

1.包依赖： requests

2.使用过程中，打开Main.py 文件，在用户参数定义区域进行一些修改。 

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
    
有啥问题欢迎提 issue或去原回答下留言。

2020.8.9
现在有点事要出去，这个版本远没有达到我的预期，只能说，恰好能工作而已，还有很多需要重构的工作，坐等后续看啥时候有空的了。