# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   main.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/11/1 23:45    1.0         None
"""

import datetime
import logging
import threading
import time

import requests
import common

import config
from cdutetc.class_timetable.data_messenger import user_login
from data_messenger import DATA_MESSENGER


class GuesserCdutetcAuto:
    def __init__(self):
        self.everyday_class_dict = None
        # self.login()
        self.activity_list = []
        self.headers = config.headers
        self.url = config.url
        self.jw_url = config.jw_url
        self.lock = threading.Lock()
        self.login_status = False

    def init(self):
        self.login()
        self.get_activity_list()

    @staticmethod
    def timetable_key_2_chinese(key):
        '''数据来自接口:/kbdy/bjkbdy_cxKbzdxsxx.html'''
        switch_list = [
            {
                "ZDM": "sj",
                "SFXS": "1",
                "ZDMC": "时间"
            },
            {
                "ZDM": "cd",
                "SFXS": "1",
                "ZDMC": "场地"
            },
            {
                "ZDM": "js",
                "SFXS": "1",
                "ZDMC": "教师"
            },
            {
                "ZDM": "jszc",
                "SFXS": "0",
                "ZDMC": "教师职称"
            },
            {
                "ZDM": "jxb",
                "SFXS": "1",
                "ZDMC": "教学班"
            },
            {
                "ZDM": "xkbz",
                "SFXS": "1",
                "ZDMC": "选课备注"
            },
            {
                "ZDM": "kcxszc",
                "SFXS": "1",
                "ZDMC": "课程学时组成"
            },
            {
                "ZDM": "zhxs",
                "SFXS": "1",
                "ZDMC": "周学时"
            },
            {
                "ZDM": "zxs",
                "SFXS": "1",
                "ZDMC": "总学时"
            },
            {
                "ZDM": "khfs",
                "SFXS": "1",
                "ZDMC": "考核方式"
            },
            {
                "ZDM": "xf",
                "SFXS": "1",
                "ZDMC": "学分"
            },
            {
                "ZDM": "xq",
                "SFXS": "1",
                "ZDMC": "校区"
            },
            {
                "ZDM": "zxxx",
                "SFXS": "0",
                "ZDMC": "在线信息"
            },
            {
                "ZDM": "skfsmc",
                "SFXS": "0",
                "ZDMC": "授课方式"
            },
            {
                "ZDM": "jxbzc",
                "SFXS": "1",
                "ZDMC": "教学班组成"
            },
            {
                "ZDM": "cxbj",
                "SFXS": "0",
                "ZDMC": "重修标记"
            },
            {
                "ZDM": "zfj",
                "SFXS": "0",
                "ZDMC": "主辅讲"
            },
            {
                "ZDM": "kcxz",
                "SFXS": "0",
                "ZDMC": "课程性质"
            },
            {
                "ZDM": "kcbj",
                "SFXS": "0",
                "ZDMC": "课程标记"
            },
            {
                "ZDM": "kczxs",
                "SFXS": "0",
                "ZDMC": "课程总学时"
            },
            {
                "ZDM": "ksfs",
                "SFXS": "0",
                "ZDMC": "考试方式"
            }
        ]
        for item in switch_list:
            if item["ZDM"] == key:
                return item["ZDMC"]
        return key

    @common.retry
    def get_activity_list(self) -> bool:
        if not self.login_status:
            return False
        r = requests.get(f"{self.jw_url}{self.main_page_location}",
                         headers=self.headers,
                         cookies=self.cookies).text
        self.activity_list = []
        for i in common.ProcessHtmlResponse.get_element_details(
                common.ProcessHtmlResponse.get_element(r, ["a"], False)[0],
                ["onclick"]):
            self.activity_list.append(common.ProcessHtmlResponse.process_js_arguments(i[0]))
        # print(self.activity_list)
        return True

    @common.retry
    def get_xq_year_and_month(self) -> bool:
        if not self.login_status:
            return False
        r = requests.post(f"{self.jw_url}/xtgl/index_cxAreaOne.html",
                          headers=self.headers,
                          cookies=self.cookies).text
        result = common.ProcessHtmlResponse.get_element_details(
            common.ProcessHtmlResponse.get_element(r, ["input"], False)[0], ["value"])
        if len(result) != 6:
            logging.warning("获取学期信息可能有异常")
        self.xq_year = result[2][0]
        self.xq_month = result[3][0]
        return True

    @common.retry
    def get_timetable(self) -> bool:
        if not self.login_status:
            return False
        param = ''
        for i in self.activity_list:
            if i[2] == "个人课表查询":
                param = i[0]
        params = {
            "gnmkdm": param
        }
        payload = {
            "xnm": self.xq_year,
            "xqm": self.xq_month,
            "kzlx": "ck",
            "xsdm": "",
            "kclbdm": ""
        }
        r = requests.post(f"{self.jw_url}/kbcx/xskbcx_cxXsgrkb.html", params=params,
                          data=payload, headers=self.headers, cookies=self.cookies).json()
        self.timetable = r["kbList"]
        return True

    @common.retry
    def get_xq_start(self) -> bool:
        if not self.login_status:
            return False
        result, path = "", "/kbcx/xskbcxZccx_cxXskbcxIndex.html"
        for i in self.activity_list:
            if i[2] == "学生课表查询（按周次）":
                result = i[0]
                path = i[1]
        params = {
            "gnmkdm": result,
            "layout": "default"
        }
        r = requests.get(f"{self.jw_url}{path}",
                         headers=self.headers,
                         cookies=self.cookies,
                         params=params).text
        start_at_list = common.ProcessHtmlResponse.get_element(r, ["option"])[0]
        start_at = ""
        # 第一个即为开学日期
        for i in start_at_list:
            if i.startswith("1("):
                start_at = i
                break
        self.start_at = common.process_start_at(start_at)
        return True

    def process_timetable_to_days(self):
        if not self.timetable:
            logging.warning("课表尚未获取")
            return
        class_dict = {}
        week_chinese_to_int = {
            "星期一": 0, "星期二": 1, "星期三": 2,
            "星期四": 3, "星期五": 4, "星期六": 5,
            "星期日": 6
        }
        start_at = self.start_at
        start_at_week = start_at.weekday()
        if start_at_week > 0:
            start_at = start_at - datetime.timedelta(days=start_at_week)
        for item in self.timetable:
            teaching_list = common.process_teaching_week(item.get("zcd", "未知"))
            sequence = common.process_teaching_sequence(item.get("jcs"))
            for t in teaching_list:
                # 实际测试偏差一周，应该是按0周开算导致的问题，暂时-1解决
                the_time = (start_at + datetime.timedelta(weeks=t-1, days=week_chinese_to_int[item.get("xqjmc")])).date()
                if the_time not in class_dict:
                    class_dict[the_time] = []
                class_dict[the_time].append({
                    "name": item.get("kcmc", "未知"),
                    "sequence": sequence,
                    "classroom": item.get("cdmc", "未知"),
                    "teacher": item.get("xm", "未知"),
                    "method": item.get("khfsmc", "未知")
                })
        with self.lock:
            self.everyday_class_dict = class_dict

    def get_today_class(self):
        if self.everyday_class_dict is None:
            self.refresh_timetable()
        with self.lock:
            if not self.everyday_class_dict:
                logging.warning("每日课程列表尚未获取或处理")
                return False, None
            today = datetime.date.today()
            if today not in self.everyday_class_dict:
                return False, None
            return True, self.everyday_class_dict[today]

    def get_now_class(self):
        success, result = self.get_today_class()
        if not success:
            return success, result
        morning = [1,2,3,4]
        afternoon = [5,6,7,8]
        night = [9,10,11,12]
        now = datetime.datetime.now().hour
        if 7 <= now <= 12:
            time_stage = morning
        elif 12 < now <= 18:
            time_stage = afternoon
        elif 18 <= now <= 24:
            time_stage = night
        else:
            return True, None
        class_now = []

        for item in result:
            if item["sequence"][0] in time_stage:
                class_now.append(item)

        return True, class_now

    def get_class_after_days(self, days:int):
        if self.everyday_class_dict is None:
            self.refresh_timetable()
        if not self.everyday_class_dict:
            logging.warning("每日课程列表尚未获取或处理")
            return False, None
        today = datetime.date.today() + datetime.timedelta(days=days)
        if today not in self.everyday_class_dict:
            return False, None
        return True, self.everyday_class_dict[today]

    def get_str_date_class(self, str_date: str):
        if self.everyday_class_dict is None:
            self.refresh_timetable()
        with self.lock:
            if not self.everyday_class_dict:
                logging.warning("每日课程列表尚未获取或处理")
                return False, None
            date = datetime.datetime.strptime(str_date, "%Y-%m-%d").date()
            if date not in self.everyday_class_dict:
                return False, None
            return True, self.everyday_class_dict[date]

    def login(self):
        result = DATA_MESSENGER.get_login_result()
        # result = login.GuesserLogin(user_config.username, user_config.password).run()
        self.login_status = False
        if result:
            self.login_status = result.login_status
            self.cookies = result.cookies
            self.user_real_name = result.user_real_name
            self.user_role = result.user_role
            self.major = result.major
            self.main_page_location = result.main_page_location
        return self.login_status

    @common.retry
    def refresh_timetable(self):
        if not self.login_status:
            self.init()
        try:
            if not self.get_activity_list():
                raise Exception("活动列表获取失败")
        except Exception as e:
            logging.error(e)
            logging.info("正在尝试重新登录")
            user_login()
            self.init()
            if not self.login_status:
                return False
        if not self.get_xq_year_and_month():
            return False
        if not self.get_timetable():
            return False
        if not self.get_xq_start():
            return False
        self.process_timetable_to_days()
        return True

    def get_everyday_class(self):
        if self.everyday_class_dict is None:
            self.refresh_timetable()
        result = {}
        with self.lock:
            for key, value in self.everyday_class_dict.items():
                result[str(key)] = value
            return result

    def run(self):
        if not self.login_status:
            logging.info("请先登录")
            return False
        return self.refresh_timetable()


def before_run():
    msg = '''本项目旨在帮助用户自动登录学校官网以获取其本人课程表信息，并在获得用户授权的前提下自动更新 Token 与课程表数据。在使用本项目之前，请仔细阅读本免责声明。使用本项目即表示您已充分理解并同意以下条款：
用途限制
本项目仅供学习、研究及个人使用。项目使用的所有自动化操作（包括登录、数据获取与更新）均应由用户本人授权并仅限访问其自身的账户与数据。严禁将本项目用于任何未经授权的账号访问、数据抓取、信息收集或其他破坏性行为。
用户责任
用户应自行确保其使用本项目的行为符合当地法律法规以及学校官网的使用条款。因用户违规使用本项目所引发的任何法律责任、账号封禁或其他后果，均由用户自行承担，与本项目作者无关。
数据安全与隐私
本项目不收集、不存储任何用户的登录凭证或个人隐私数据。所有相关数据均保存在用户本地设备或用户自行指定的位置。用户需自行承担其个人数据安全风险。
风险提示
自动化登录及访问行为可能存在被学校官网系统识别、阻断或封禁的风险。本项目作者不对因系统更新、接口变更、封禁策略调整等导致的任何功能失效或数据错误负责。
无担保声明
本项目按“现状”提供，不提供任何形式的明示或暗示担保，包括但不限于项目的可用性、稳定性、安全性或适用性。使用本项目造成的任何直接或间接损失（包括但不限于数据丢失、账号异常、设备损坏等），均由用户自行承担。
免责声明变更
本免责声明可能随项目更新而调整。用户在继续使用项目时，即视为接受更新后的声明内容。


我已阅读并充分理解本免责声明的全部内容，并知晓使用本项目可能带来的相关风险。\n运行、使用、编译、修改、调试、逆向分析或以任何方式操作本项目，即表示我已同意并接受本免责声明的全部条款，并自愿承担因使用本项目可能产生的一切后果。'''
    print(msg)
    input("回车键继续运行")


if __name__ == '__main__':
    # before_run()
    logging.info("欢迎使用Guesser课程表小助手")
    app = GuesserCdutetcAuto()
    app.run()
    time.sleep(0.1)
    input("回车键退出")
