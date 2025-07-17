# YouTube视频分析处理

## 介绍
此项目是用于通过 Gemini 模型对 YouTube 视频进行理解分析, 然后将分析结果与指定时间段的美股股市数据进行对比分析, 最终生成分析报告。  

报告中可能包含以下内容：
- 视频内容概述
- 视频中提到的公司或股票
- 视频中提到的事件或新闻
- 视频中提到的分析师观点
- 视频中提到的市场趋势
- 形成类似高盛和摩根大通风格的投资建议报告

**除了对单个视频分析之外, 还可以对指定 YouTube 的视频批量分析, 最多10个视频。(Gemini 模型限制)**   


### 通过 Gemini 模型分析视频

Gemini API 和 AI Studio 支持将 YouTube 网址作为文件数据 Part。您可以添加 YouTube 网址，并附上提示，要求模型对视频内容进行总结、翻译或以其他方式进行互动。

限制：

- 对于免费层级，您每天上传的 YouTube 视频时长不得超过 8 小时。
- 对于 2.5 之前的型号，每个请求只能上传 1 个视频。对于 2.5 之后的模型，每个请求最多可以上传 10 个视频。
- 您只能上传公开视频（而非私享视频或不公开列出的视频）。

#### 添加 YouTube 网址
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{
        "parts":[
            {"text": "Please summarize the video in 3 sentences."},
            {
              "file_data": {
                "file_uri": "https://www.youtube.com/watch?v=9hE5-98ZeCg"
              }
            }
        ]
      }]
    }' 2> /dev/null
```

#### 转写视频并提供视觉描述
```bash
PROMPT="Transcribe the audio from this video, giving timestamps for salient events in the video. Also provide visual descriptions."
```


### 通过 YouTube 频道名称获取视频列表

#### 参数
- channel_id: 频道ID或频道名称，如果是频道名称，则需要在前面加上 @ 符号，例如：@LinusTechTips。
- lang: 视频结果语言代码，默认为 en-US，任何语言代码均可，当提交不支持的语言代码时，默认使用 en-US 作为语言代码。
- sortBy: 排序方式，默认为 newest，可选值为 newest 和 oldest 和 mostPopular：
  - newest: 按照最新排序，默认值。
  - oldest: 按照最旧排序。
- mostPopular: 按照最热排序。
- contentType: 内容类型，默认为 videos，可选值为 videos 和 shorts 和 live：
  - videos: 视频列表，默认值。
  - shorts: 短视频列表。
  - live: 直播列表。
- nextToken: 用于继续获取视频的令牌。可选参数，默认值为空，从第一页开始获取。
  - 如果获取第一页，则nextToken参数为None。
  - 如果获取第二页，则nextToken参数为第一页请求返回的nextToken。

#### 获取视频列表示例
```bash
curl --location --request GET 'https://api.tikhub.io/api/v1/youtube/web/get_channel_videos_v2?channel_id=@MarketBeatMedia&lang=zh-CN&sortBy=newest&contentType=videos&nextToken' \
--header 'Authorization: Bearer <API KEY>'
```

#### 返回数据
频道视频列表，包含视频ID、标题、缩略图、观看次数、点赞次数、评论数、视频时长等信息。   


### 获取指定日期范围的美股数据

#### 输入参数
```
名称	类型	必选	描述   
ts_code	str	N	股票代码（e.g. AAPL）   
trade_date	str	N	交易日期（YYYYMMDD）   
start_date	str	N	开始日期（YYYYMMDD）   
end_date	str	N	结束日期（YYYYMMDD） 
```  

#### 返回参数
```
名称	类型	默认显示	描述   
ts_code	str	Y	股票代码   
trade_date	str	Y	交易日期   
close	float	Y	收盘价   
open	float	Y	开盘价   
high	float	Y	最高价   
low	float	Y	最低价   
pre_close	float	Y	昨收价   
change	float	N	涨跌额   
pct_change	float	Y	涨跌幅   
vol	float	Y	成交量   
amount	float	Y	成交额   
vwap	float	Y	平均价   
turnover_ratio	float	N	换手率   
total_mv	float	N	总市值   
pe	float	N	PE   
pb	float	N	PB   
```

#### Python代码示例
```python
# 导入tushare
import tushare as ts
# 初始化pro接口
pro = ts.pro_api('xxxx')

# 拉取数据
df = pro.us_daily(**{
    "ts_code": "AAPL",
    "trade_date": "",
    "start_date": "20190101",
    "end_date": "20190904",
    "offset": "",
    "limit": ""
}, fields=[
    "ts_code",
    "trade_date",
    "close",
    "open",
    "high",
    "low",
    "pre_close",
    "pct_change",
    "vol",
    "amount",
    "vwap",
    "change"
])
print(df)
```

#### 返回数据示例
```
 ts_code trade_date   close    open    high     low pre_close pct_change       vol              amount    vwap
0      AAPL   20190904  209.19  208.39  209.48  207.32    205.70       1.70  19216821   4008342529.970000  208.59
1      AAPL   20190903  205.70  206.43  206.98  204.22    208.74      -1.46  20059575   4120106317.760000  205.39
2      AAPL   20190830  208.74  210.16  210.45  207.20    209.01      -0.13  21162563   4410472824.780000  208.41
3      AAPL   20190829  209.01  208.50  209.32  206.66    205.53       1.69  21007653   4380322743.230000  208.51
4      AAPL   20190828  205.53  204.10  205.72  203.32    204.16       0.67  15957633   3269889907.950000  204.91
..      ...        ...     ...     ...     ...     ...       ...        ...       ...                 ...     ...
165    AAPL   20190108  150.75  149.56  151.82  148.52    147.93       1.91  41025313   6159076907.780000  150.13
166    AAPL   20190107  147.93  148.70  148.83  145.90    148.26      -0.22  54777766   8071925608.900000  147.36
167    AAPL   20190104  148.26  144.53  148.55  143.80    142.19       4.27  58607071   8605786116.450000  146.84
168    AAPL   20190103  142.19  143.98  145.72  142.00    157.92      -9.96  91312188  13108586866.810000  143.56
169    AAPL   20190102  157.92  154.89  158.85  154.23    157.74       0.11  37039739   5814198206.330000  156.97
```
