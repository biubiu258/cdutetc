# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   login.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/11/1 23:45    1.0         None
"""
import time
from dataclasses import dataclass
import ddddocr
import requests
import numexpr
import encrypt
import common
import user_config
import logging
import config


@dataclass
class LoginResult:
    login_status: bool
    cookies: dict | None
    user_real_name: str | None
    user_role: str | None
    major: str | None
    main_page_location: str | None
    activity_list: list[list[str]] | None


class GuesserLogin:
    def __init__(self, username, password):
        self.cookies = None
        self.url = config.url
        self.jw_url = config.jw_url
        self.headers = config.headers
        self.username = username
        self.password = password
        self.activity_list = []

    @common.retry
    def get_activity_list(self) -> bool:
        r = requests.get(f"{self.jw_url}{self.main_page_location}",
                         headers=self.headers,
                         cookies=self.cookies).text
        self.activity_list = []
        for i in common.ProcessHtmlResponse.get_element_details(
                common.ProcessHtmlResponse.get_element(r, ["a"], False)[0],
                ["onclick"]):
            self.activity_list.append(common.ProcessHtmlResponse.process_js_arguments(i[0]))
        logging.info("获取活动列表成功")
        return True

    @staticmethod
    def timestamp(long_type=False) -> str:
        if long_type:
            return str(int(time.time() * 1000))
        return str(int(time.time()))

    @common.retry
    def get_captcha(self):
        params = {
            "_t": self.timestamp(),
            "uid": ""
        }
        logging.info("正在获取验证码,机房或者国外ip无法正常获取到,请使用家宽")
        r = requests.get(f"{self.url}/lyuapServer/kaptcha", params=params, headers=self.headers,timeout=10).json()
        logging.info(
            "获取人机验证成功 超时时间: {} | 验证类型: {}".format(r.get("timeout", 0), r.get("kaptchaType", "未知")))
        captcha_id = r["uid"]
        captcha = r["content"].split(",", 1)[1]
        # 0易被识别为o
        captcha_ocr = ddddocr.DdddOcr(show_ad=False).classification(captcha).replace("=", "").replace("o", "0")
        result = numexpr.evaluate(captcha_ocr)
        logging.info(f"处理验证码成功:{captcha_ocr} = {result}")
        return captcha_id, result

    @staticmethod
    def process_login_res(res: dict) -> bool:
        fail_dict = {"PASSERROR": "密码错误",
                     "NOUSER": "用户不存在",
                     "CODEFALSE": "验证码不正确"}
        if "data" in res:
            logging.info("登录失败 {}".format(fail_dict.get(res["data"].get("code", "未知异常"),
                                                            res["data"].get("code", res["data"]))))
            if res["data"].get("code", "") == "PASSERROR":
                logging.info("密码失败次数: {}".format(res["data"].get("data", "未知")))
            return False
        if "ticket" in res:
            logging.info("ticket 获取成功")
            return True
        logging.info("登录失败 无法处理的响应: {}".format(res))
        return False

    @common.retry
    def login(self) -> bool:
        if self.username == "用户名" or self.username == "" or self.username is None:
            logging.error("请先设置用户名与密码！")
            logging.info("请输入账号(学号)")
            self.username = input("")
            logging.info("请输入密码")
            self.password = input("")
            # return False
        logging.info("正在尝试登录,若程序卡死或响应超时,说明学校服务器被关闭(一般在24:00以后就无法访问了)")
        captcha_id, result = self.get_captcha()
        payload = {
            "username": self.username,
            "password": encrypt.js_encrypt_string(self.password),
            "service": f"{self.jw_url}/sso/lyiotlogin",
            "loginType": "",
            "id": captcha_id,
            "code": str(result)
        }
        r = requests.post(f"{self.url}/lyuapServer/v1/tickets", data=payload, headers=self.headers, timeout=10).json()
        if not self.process_login_res(r):
            self.username = None
            self.password = None
            return self.login()
        self.jw_login(r["ticket"])
        # 验证是否登录成功
        if self.get_user_real_name():
            return True
        logging.info(f"登录失败 {self.username[:4]}***{self.username[-4:]}")
        self.get_activity_list()
        raise Exception("重试中....")
        return False

    @common.retry
    def jw_login(self, ticket):
        self.headers["Referer"] = self.url
        params = {"ticket": ticket}
        r = requests.get(f"{self.jw_url}/sso/lyiotlogin", params=params,
                         headers=self.headers,
                         allow_redirects=False).headers
        self.cookies = common.process_set_cookie(r["set-cookie"])
        logging.info("教务系统 首次请求cookies成功")
        logging.debug("cookies: {}".format(self.cookies))
        r = requests.get(f"{self.jw_url}/sso/lyiotlogin",
                         headers=self.headers,
                         cookies=self.cookies,
                         allow_redirects=False).headers
        logging.info("教务系统 第一跳成功")
        logging.debug("location: {}".format(r["location"]))
        del self.cookies["JSESSIONID"]
        r = requests.get(r["location"], headers=self.headers,
                         cookies=self.cookies,
                         allow_redirects=False).headers
        logging.info("教务系统 第二跳成功")
        self.main_page_location = r["location"]
        # 记录原route
        route = self.cookies.get("route", "")
        self.cookies = common.process_set_cookie(r["set-cookie"])
        self.cookies["route"] = route
        del self.cookies["rememberMe"]
        logging.info("教务系统 获取最终cookies成功")
        logging.debug("cookies: {}".format(self.cookies))
        return True

    @common.retry
    def get_user_real_name(self):
        params = {
            "xt": "jw",
            "localeKey": "zh_CN",
            "_": self.timestamp(True),
            "gnmkdm": "index"
        }
        r = requests.get(f"{self.jw_url}/xtgl/index_cxYhxxIndex.html",
                         params=params,
                         headers=self.headers,
                         cookies=self.cookies).text
        stu_name, major = common.ProcessHtmlResponse.get_element(r, ["h4", "p"])
        if not stu_name or not major:
            logging.error("登录失败")
            return False
        self.user_real_name = stu_name[0].split("  ")[0]
        self.user_role = stu_name[0].split("  ")[1]
        self.major = major[0]
        logging.info(f"登录成功 {self.user_role} {self.user_real_name} {self.major}")
        return True

    def get_login_cookies(self) -> dict:
        return self.cookies

    def get_user_details(self) -> tuple[str, str, str]:
        return self.user_real_name, self.user_role, self.major

    def run(self):
        if self.login():
            return LoginResult(True, self.get_login_cookies(), *self.get_user_details(),
                               self.main_page_location,self.activity_list)
        return LoginResult(False, None,
                           None, None, None, None,None)
