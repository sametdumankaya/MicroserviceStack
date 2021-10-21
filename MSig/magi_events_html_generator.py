import json
import requests
import datetime

url = 'http://localhost:5000/Events/PostEvents'

headers = {'accept': 'application/json'}
htmlData=[
  {
    "eventDateTimeStampEpochs": int(datetime.datetime.now().timestamp() * 1000),
    "htmlData": "<h1>HTML Ipsum Presents</h1>\n\n <br /><img src=\"https://finance.hatredio.design/wp-content/uploads/2018/03/59e6decaf0bf1f0001c98986_finance-tax.jpg\" width=\"400\" height=\"200\"> <br /> <br />\n\n<p><strong>Pellentesque habitant morbi tristique</strong> senectus et netus et malesuada fames ac turpis egestas. Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu libero sit amet quam egestas semper. <em>Aenean ultricies mi vitae est.</em> Mauris placerat eleifend leo. Quisque sit amet est et sapien ullamcorper pharetra. Vestibulum erat wisi, condimentum sed, <code>commodo vitae</code>, ornare sit amet, wisi. Aenean fermentum, elit eget tincidunt condimentum, eros ipsum rutrum orci, sagittis tempus lacus enim ac dui. <a href=\"#\">Donec non enim</a> in turpis pulvinar facilisis. Ut felis.</p>\n\n<h2>Header Level 2</h2>\n\n<ol>\n   <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit.</li>\n   <li>Aliquam tincidunt mauris eu risus.</li>\n</ol>\n\n<blockquote><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus magna. Cras in mi at felis aliquet congue. Ut a est eget ligula molestie gravida. Curabitur massa. Donec eleifend, libero at sagittis mollis, tellus est malesuada tellus, at luctus turpis elit sit amet quam. Vivamus pretium ornare est.</p></blockquote>\n\n<h3>Header Level 3</h3>\n\n<ul>\n   <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit.</li>\n   <li>Aliquam tincidunt mauris eu risus.</li>\n</ul>",
    "newsTitle": "MagiFinance Example News Title",
    "indicators": [
      {
        "symbol": "BIIB",
        "volume": 430,
        "price": 664,
        "eventRole": "Leading Indicator"
      },
      {
        "symbol": "OTEX",
        "volume": 340,
        "price": 231,
        "eventRole": "Leading Indicator"
      },
      {
        "symbol": "CMC",
        "volume": 102,
        "price": 887,
        "eventRole": "Leading Indicator"
      },
      {
        "symbol": "AMKR",
        "volume": 77,
        "price": 110,
        "eventRole": "Main Indicator"
      },
      {
        "symbol": "CATY",
        "volume": 531,
        "price": 664,
        "eventRole": "Main Indicator"
      },
      {
        "symbol": "FMBI",
        "volume": 341,
        "price": 567,
        "eventRole": "Main Indicator"
      },
      {
        "symbol": "MTX",
        "volume": 334,
        "price": 234,
        "eventRole": "Trailing Indicator"
      },
      {
        "symbol": "SGEN",
        "volume": 676,
        "price": 223,
        "eventRole": "Trailing Indicator"
      },
      {
        "symbol": "LYV",
        "volume": 341,
        "price": 752,
        "eventRole": "Trailing Indicator"
      }
    ]
  }
]
response = requests.post(url,headers=headers,json=htmlData)

print(response)
