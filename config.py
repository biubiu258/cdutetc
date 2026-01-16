# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   config.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/11/2 0:15    1.0         开发者配置
"""
import os
DEBUG = False


# retry
# 最大重试次数
total_retry = 3
# 重试等待时间
wait_time = 5
url = "https://ac.cdutetc.cn"
jw_url = "https://jwgl.cdutetc.cn"
headers = {
  "Connection": "keep-alive",
  "sec-ch-ua-mobile": "?0",
  "loginToken": "loginToken",
  "X-Requested-With": "XMLHttpRequest",
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 "
                "Safari/537.36 Edg/141.0.0.0",
  "Accept": "application/json, text/plain, */*",
  "Sec-Fetch-Site": "same-origin",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Dest": "empty",
  "Referer": "https://ac.cdutetc.cn/lyuapServer/login?service=https%3A%2F%2Fjwgl.cdutetc.cn%2Fsso%2Flyiotlogin",
  "Accept-Encoding": "gzip, deflate, br, zstd",
  "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
}

# 证书
if DEBUG:
    os.environ['REQUESTS_CA_BUNDLE'] = r'D:\reqable-ca.pem'
    print("##调试模式已启用")
