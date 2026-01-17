# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   score_query.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/12/26 15:05    1.0         None
"""
import logging
import time

from requests import Response
from data_messenger import DATA_MESSENGER
import requests
import common
import config
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date
import threading


def get_academic_year_and_semester(
    now: datetime | None = None,
    second_semester_month: int = 2,
    second_semester_day: int = 15
):
    if now is None:
        now = datetime.now()

    year = now.year
    month = now.month
    today = now.date()

    # 学年判断
    if month >= 9:
        start_year = year
        end_year = year + 1
    else:
        start_year = year - 1
        end_year = year

    # 第二学期开始日期（在 end_year）
    second_semester_start = date(end_year, second_semester_month, second_semester_day)

    # 学期判断
    semester = 2 if today >= second_semester_start else 1

    return f"{start_year}-{end_year}", semester


@dataclass
class GradeRecord:
    course_name: str
    academic_year: str            # 学年
    semester: str                 # 学期
    course_nature: str            # 课程性质
    credits: float                # 学分
    # grade_remark: Optional[str]   # 成绩备注
    gpa: float                    # 绩点
    grade_type: str               # 成绩性质
    # is_degree_course: bool        # 是否学位课程
    # offering_college: str         # 开课学院
    # course_tag: Optional[str]     # 课程标记
    course_category: str          # 课程类别
    # course_affiliation: str       # 课程归属
    teaching_class: str           # 教学班
    instructor: str               # 任课教师
    assessment_method: str        # 考核方式
    # student_id: str               # 学号
    # name: str                     # 姓名
    # student_tag: Optional[str]    # 学生标记
    grade: float                  # 成绩
    is_grade_invalid: bool        # 是否成绩作废
    credit_gpa: float             # 学分绩点

    def print_details(self):
        print("========== 成绩记录 ==========")
        print(f"课程名称 ：{self.course_name}")
        print(f"学年 / 学期 : {self.academic_year} {self.semester}")
        print(f"课程性质   : {self.course_nature}")
        print(f"课程类别   : {self.course_category}")
        print(f"教学班     : {self.teaching_class}")
        print(f"任课教师   : {self.instructor}")
        print(f"考核方式   : {self.assessment_method}")
        print("-" * 30)
        print(f"学分       : {self.credits}")
        print(f"成绩       : {self.grade}")
        print(f"绩点       : {self.gpa}")
        print(f"学分绩点   : {self.credit_gpa}")
        print(f"成绩性质   : {self.grade_type}")
        print(f"成绩作废   : {'是' if self.is_grade_invalid else '否'}")
        print("==============================")

    @staticmethod
    def red(msg):
        return f"\033[1;31m{msg}\033[0m"

    def simple_print(self):
        print(self.simple_to_string())

    def simple_to_string(self):
        return (f"{self.course_name} | "
            f"{'及格' if self.grade >= 60 and not self.is_grade_invalid else self.red('挂科')} | "
            f"{self.academic_year} {self.semester} | "
            f"{self.grade_type} | "
            f"{self.credits}学分 | "
            f"成绩:{self.grade} | "
            f"绩点:{self.gpa} | "
            f"{'作废' if self.is_grade_invalid else '有效'}")

    def simple_to_email_html(self) -> str:
        status = "及格" if self.grade >= 60 and not self.is_grade_invalid else "挂科"
        validity = "作废" if self.is_grade_invalid else "有效"

        color = "#28a745" if status == "及格" else "#dc3545"

        return f"""
        <div style="border:1px solid #eee;padding:10px;margin-bottom:10px;">
            <strong>{self.course_name}</strong><br>
            学年学期：{self.academic_year} {self.semester}<br>
            成绩类型：{self.grade_type}<br>
            学分：{self.credits}<br>
            成绩：<span style="color:{color};font-weight:bold;">{self.grade}（{status}）</span><br>
            绩点：{self.gpa}<br>
            状态：{validity}
        </div>
        """


@dataclass
class CourseHistoryRecord:
    course_code: str              # 课程代码
    course_name: str              # 课程名称
    grade_record: Optional[list[GradeRecord]] = None    # 课程具体信息
    is_passed: Optional[bool] = None
    max_grade: Optional[float] = None
    failed_count: Optional[int] = None
    succeeded_count: Optional[int] = None
    max_info: Optional[GradeRecord] = None
    max_credits: Optional[float] = 0.0
    course_category: Optional[str] = None

    def simple_print(self):
        print(
            f"{self.course_name} | "
            f"最高成绩：{self.max_grade} | "
            f"挂科次数：{self.failed_count} | "
            f"及格次数：{self.succeeded_count}"
        )


class HistoryManager:
    def __init__(self):
        self.course_history_record_list = []
        self.data_lock = threading.Lock()

    def clear_course_history_record_list(self):
        with self.data_lock:
            self.course_history_record_list.clear()

    def find_course_by_course_code(self, course_code: str) -> Optional[CourseHistoryRecord]:
        with self.data_lock:
            for record in self.course_history_record_list:
                if record.course_code == course_code:
                    return record
            return None

    def add_course_history_record(self, course_code, course_name):
        with self.data_lock:
            self.course_history_record_list.append(CourseHistoryRecord(course_code, course_name,grade_record=[]))

    def add_grade_record(self, course_code, grade_record)->bool:
        with self.data_lock:
            for record in self.course_history_record_list:
                if record.course_code == course_code:
                    record.grade_record.append(grade_record)
                    return True
            return False

    def auto_add_grade_record(self, course_code, course_name, grade_record)->bool:
        if not self.find_course_by_course_code(course_code):
            self.add_course_history_record(course_code, course_name)
        return self.add_grade_record(course_code, grade_record)

    def grade_info_add_to_course_history_record(self, grade_info)->bool:
        return self.auto_add_grade_record(*self.grade_info_to_grade_record(grade_info))

    def auto_analyze_course_history_record(self):
        with self.data_lock:
            for record in self.course_history_record_list:
                self.analyze_course(record)

    def get_grade_list_semester(self, academic_year, semester)->list[GradeRecord]:
        semester = str(semester)
        result = []
        with self.data_lock:
            for record in self.course_history_record_list:
                for grade_record in record.grade_record:
                    if grade_record.academic_year == academic_year and grade_record.semester == semester:
                        result.append(grade_record)
            return result

    def accumulate_credits(self, only_compulsory=True):
        total = 0
        failed = 0
        succeeded = 0
        total_failed = 0
        with self.data_lock:
            for record in self.course_history_record_list:
                if only_compulsory:
                    if record.course_category != "必修课":
                        continue
                total += record.max_credits
                if record.is_passed:
                    succeeded += record.max_credits
                else:
                    failed += record.max_credits
                if record.failed_count > 0:
                    total_failed += record.max_credits
        return total, failed, succeeded, total_failed

    @staticmethod
    def grade_info_to_grade_record(grade_info:dict) -> tuple[str, str, GradeRecord]:
        course_code = grade_info.get("kch", "未知课程id")
        course_name = grade_info.get("kcmc", "未知课程名称")
        academic_year = grade_info.get("xnmmc", "未知学年")
        semester = grade_info.get("xqmmc", "未知学期")
        course_nature = grade_info.get("kcxzmc", "未知课程性质")
        credits = float(grade_info.get("xf", 0.0))
        gpa = float(grade_info.get("jd", 0.0))
        grade_type = grade_info.get("ksxz", "未知课程性质")
        # is_degree_course = grade_info.get("")
        # offering_college: str  # 开课学院
        # course_tag: Optional[str]  # 课程标记
        course_category = grade_info.get("kclbmc","未知课程类别")
        # course_affiliation: str  # 课程归属
        teaching_class = grade_info.get("jxbmc","未知教学班名称")
        instructor = grade_info.get("jsxm", "未知教师名称")
        assessment_method = grade_info.get("khfsmc", "未知考核方式")
        grade = float(grade_info.get("cj", 0.0))
        is_grade_invalid = False if grade_info.get("cjsfzf", "未知是否作废") == "否" else True
        credit_gpa = float(grade_info.get("xfjd", 0.0))
        result = GradeRecord(course_name, academic_year, semester, course_nature,credits, gpa, grade_type,
                             course_category, teaching_class, instructor, assessment_method,
                             grade, is_grade_invalid, credit_gpa)
        return course_code, course_name, result

    @staticmethod
    def analyze_course(course_history: CourseHistoryRecord):
        failed_count = 0
        succeeded_count = 0
        max_grade = 0
        max_credits = 0
        max_info = None
        for grade_record in course_history.grade_record:
            if grade_record.is_grade_invalid:
                failed_count += 1
                continue
            if grade_record.credits > max_credits:
                max_credits = grade_record.credits
            if grade_record.grade >= max_grade:
                max_grade = grade_record.grade
                max_info = grade_record
            if not grade_record.grade >= 60.0:
                failed_count += 1
            else:
                succeeded_count += 1
        course_history.failed_count = failed_count
        course_history.succeeded_count = succeeded_count
        course_history.max_grade = max_grade
        course_history.max_info = max_info
        course_history.is_passed = True if succeeded_count > 0 else False
        course_history.max_credits = max_credits
        course_history.course_category = max_info.course_category

    def get_history(self)->list[CourseHistoryRecord]:
        return self.course_history_record_list


class Query:
    def __init__(self):
        self.email_manager = None
        self.grade_info = None
        self.cookies = None
        self.this_semester = None
        self.history_manager = HistoryManager()
        self.is_initialized = False
        self.init_lock = threading.RLock()
        # self.worker_thread = threading.Thread(target=self.update_worker, name="Query",daemon=True,args=())
        # self.worker_thread.start()

    def set_cookies(self,cookies=None):
        if cookies:
            self.cookies = cookies
            return
        login_result = DATA_MESSENGER.get_login_result()
        if login_result:
            self.cookies = login_result.cookies
        return

    def set_email_user(self,email_user: str=None, email_password: str=None, to_user: str=None):
        if email_user and email_password and to_user:
            self.to_user = to_user
            self.email_manager = common.EmailManager(email_user=email_user, email_password=email_password)
            logging.info("邮件通知已启用")
        else:
            self.email_manager = None
            logging.info("邮件通知已禁用")

    def get_all_history(self)->list[CourseHistoryRecord]:
        with self.init_lock:
            if not self.is_initialized:
                self.init()
        return self.history_manager.get_history()

    @staticmethod
    def check_response(res:Response):
        if res.status_code != 200:
            raise Exception(f"API响应异常:{res.status_code}")
        response_json = res.json()
        if "items" not in response_json:
            raise Exception("响应异常(未有key:items)")
        return response_json

    @common.retry
    def get_grade_info(self):
        url = "https://jwgl.cdutetc.cn/cjcx/cjcx_cxXsgrcj.html"
        params = {"doType":"query","gnmkdm":""}
        payload = {
          "xnm": "",
          "xqm": "",
          "sfzgcj": "",
          "kcbj": "",
          "_search": "false",
          "nd": str(int(time.time())*1000),
          "queryModel.showCount": "5000",
          "queryModel.currentPage": "1",
          "queryModel.sortName": " ",
          "queryModel.sortOrder": "asc",
          "time": "1"
        }
        response = requests.post(url,  data=payload, headers=config.headers, params=params,cookies=self.cookies)
        self.grade_info = self.check_response(response)

    @common.retry
    def query_retake_paid(self):
        with self.init_lock:
            if not self.is_initialized:
                self.init()
        url = "https://jwgl.cdutetc.cn/paycenter/paycenter_cxGrjfIndex.html"
        params = {"doType":"query","gnmkdm":""}
        payload = {
              "xnm": "",
              "xqm": "",
              "sfqr": "1",
              "flg": "1",
              "_search": "false",
              "queryModel.showCount": "500",
              "queryModel.currentPage": "1",
              "queryModel.sortName": " ",
              "queryModel.sortOrder": "asc",
              "time": "1"
            }
        response = requests.post(url, data=payload, headers=config.headers, params=params, cookies=self.cookies)
        return self.check_response(response)["items"]

    @staticmethod
    def process_total_retake_paid(total_retake_paid:list):
        result = 0.0
        for r in total_retake_paid:
            result += float(r["order_amount"])
        return result

    def get_this_semester(self):
        with self.init_lock:
            if not self.is_initialized:
                self.init()
        return self.this_semester

    def accumulate_credits(self):
        with self.init_lock:
            if not self.is_initialized:
                self.init()
        return self.history_manager.accumulate_credits()

    def update_history_records(self):
        self.history_manager.clear_course_history_record_list()
        for item in self.grade_info['items']:
            self.history_manager.grade_info_add_to_course_history_record(item)
        self.history_manager.auto_analyze_course_history_record()

    def update_this_semester(self):
        self.this_semester = self.history_manager.get_grade_list_semester(*get_academic_year_and_semester())

    def is_new_coming(self):
        with self.init_lock:
            if not self.is_initialized:
                self.init()
        if self.this_semester is None:
            return False
        self.get_grade_info()
        self.update_history_records()
        new_history = self.history_manager.get_grade_list_semester(*get_academic_year_and_semester())
        if len(new_history) != len(self.this_semester):
            self.update_this_semester()
            return True

    def send_notify(self, notify: str | list, for_email: bool = False):
        if isinstance(notify, list):
            if for_email:
                result = "".join(n.simple_to_email_html() for n in notify)
                if self.email_manager:
                    try:
                        retake_total_paid = self.process_total_retake_paid(self.query_retake_paid())
                    except Exception as e:
                        logging.error(e)
                        retake_total_paid = 0.0
                    self.email_manager.send_email(self.to_user, result, retake_total_paid,
                                                  *self.history_manager.accumulate_credits(True))
                    logging.info("已发送成绩更新邮件")
                return result
            else:
                return "\n".join(n.simple_to_string() for n in notify)
        else:
            return notify

    def update_worker(self):
        self.run()
        self.send_notify(self.this_semester,True)
        while True:
            if self.is_new_coming():
                self.send_notify(self.this_semester,True)
            time.sleep(15)

    def run(self):
        self.get_grade_info()
        self.update_history_records()
        self.update_this_semester()

    def init(self):
        self.set_cookies()
        self.run()
        with self.init_lock:
            self.is_initialized = True
