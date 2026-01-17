# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   common.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/11/2 0:11    1.0         None
"""
import datetime
import json
import os
import sys
import threading
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

import config
import logging
from bs4 import BeautifulSoup
from flask import jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import email.utils


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')


def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for i in range(config.total_retry):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == config.total_retry - 1:
                    print(
                        f"执行{func.__name__}函数发生异常[{e}],已经达到最大重试次数{i + 1}/{config.total_retry}")
                    raise
                print(f"执行{func.__name__}函数发生异常[{e}],将在{config.wait_time}s后重试,重试次数{i+1}/{config.total_retry}")
                time.sleep(config.wait_time)
    return wrapper


def process_set_cookie(cookie_str: str)->dict:
    cookies = {}
    parts = cookie_str.split(',')
    for part in parts:
        subparts = [x.strip() for x in part.split(';')]
        if subparts:
            if '=' in subparts[0]:
                key, value = subparts[0].split('=', 1)
                cookies[key] = value
    return cookies


class ProcessHtmlResponse:
    @staticmethod
    def get_element(html:str, elements:list, str_only=True)->tuple[list[str]]:
        bs = BeautifulSoup(html, 'lxml')
        result = ()
        for element in elements:
            p = bs.find_all(element)
            if str_only:
                result = result + ([i.get_text(strip=True).replace("\xa0"," ") for i in p],)
            else:
                result = result + (p,)
        return result

    @staticmethod
    def get_element_details(elements:list| tuple, targets:list)->tuple[list[str]]:
        result = ()
        for element in elements:
            target_result = []
            for target in targets:
                r = element.get(target)
                if r:
                    target_result.append(r.strip().replace("\xa0"," "))
            if target_result:
                result = result + (target_result,)
        return result

    @staticmethod
    def process_js_arguments(js_arguments:str)->list[str]:
        result = js_arguments[js_arguments.find("(")+1:js_arguments.find(")")].strip()
        return json.loads("["+result.replace("'",'"')+"]")


def process_teaching_week(week:str)->list[int,]:
    result = []
    for item in week.split(","):
        odd_flag = False
        even_flag = False
        if "单" in item:
            odd_flag = True
        if "双" in item:
            even_flag = True
        item = item[:item.rfind("周")]
        if "-" in item:
            item = item.split("-")
            for i in range(int(item[0]), int(item[1])+1):
                if i % 2 == 0 and odd_flag:
                    continue
                if i % 2 == 1 and even_flag:
                    continue
                result.append(i)
            continue
        result.append(int(item))
    return result


def process_teaching_sequence(sequence:str)->list[int]:
    result = []
    sequence = sequence.split("-")
    for i in range(int(sequence[0]), int(sequence[1])+1):
        result.append(i)
    return result


def get_start_month_and_day()->list[int,int]:
    month = datetime.datetime.now().month
    if month >= 9:
        return [9, 1]
    else:
        return [2, 1]


def process_start_at(start_at:str):
    start_at = start_at[start_at.find("(")+1:start_at.rfind("至")]
    return datetime.datetime.strptime(start_at, "%Y-%m-%d")

def real_path():
    # frozen 表示在 PyInstaller 打包环境
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    # 开发环境：返回当前脚本所在目录
    return Path(__file__).resolve().parent


class Response:
    @staticmethod
    def ok(msg="成功",data=None):
        return jsonify({"msg": msg, "data": data, "code": 200})

    @staticmethod
    def fail(msg="失败"):
        return jsonify({"msg": msg, "data": None, "code": 201})

    @staticmethod
    def server_error():
        return jsonify({"msg": "服务器内部异常,请联系管理员", "data": None, "code": 500})

    @staticmethod
    def response(msg=None, data=None, code=None):
        return jsonify({"msg": msg, "data": data, "code": code})

    @staticmethod
    def auth_required(msg="请先登录"):
        return jsonify({"msg": msg, "data": None, "code": 401})

    @staticmethod
    def forbidden():
        return jsonify({"msg": "拒绝访问", "data": None, "code": 403})

    @staticmethod
    def not_found():
        return jsonify({"msg": "资源未找到或被永久删除", "data": None, "code": 404})


def catch_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"func:{func.__name__}:{e}")
            return Response.server_error()
    return wrapper


class EmailManager:
    """邮件发送管理器"""

    def __init__(self, smtp_server: str = "smtp.qq.com", smtp_port: int = 587,
                 email_user: str = "", email_password: str = ""):
        """
        初始化邮件管理器

        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            email_user: 发件人邮箱
            email_password: 邮箱授权码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password

    def send_email(self, to_email: str, message: str, retake_total_paid=0.0,
                   credit_total: float | None = None,
                   credit_failed: float | None = None,
                   credit_succeeded: float | None = None,
                   total_failed: float | None = None,
                   title: str = '成绩更新提醒') -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart()
            # 使用formataddr正确设置发件人信息，QQ邮箱更认可这种格式
            msg['From'] = email.utils.formataddr(("Guesser小助手", self.email_user))
            # 同样使用formataddr设置收件人
            msg['To'] = email.utils.formataddr(("", to_email))
            msg['Subject'] = Header(title, 'utf-8')
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            credit_block = ""
            if credit_total is not None:
                credit_block = f"""
                <div style="border:1px solid #eee;padding:10px;margin-top:10px;">
                    <strong>📚 学分历史统计(必修课)</strong><br>
                    总学分：{credit_total}<br>
                    已通过学分：
                    <span style="color:#28a745;font-weight:bold;">
                        {credit_succeeded}
                    </span><br>
                    未通过学分：
                    <span style="color:#dc3545;font-weight:bold;">
                        {credit_failed}
                    </span>
                    </span><br>
                    历史未通过学分：
                    <span style="color:#dc3545;font-weight:bold;">
                        {total_failed}
                    </span>
                </div>
                """
            paid_tip = ""
            if retake_total_paid > 0:
                paid_tip = f"""
                <p style="color:#dc3545;">
                    💰 当前重修累计花费：
                    <strong>{retake_total_paid:.2f}</strong> 元
                </p>
                """
            html_content = f"""
            <html>
            <body style="font-family:Arial,Helvetica,sans-serif;">
                <h2>📊 成绩更新提醒</h2>

                <p>最新成绩信息：</p>

            {message}

            <hr>

            {credit_block}

            {paid_tip}

            <p style="color:#666;font-size:12px;">
                发送时间：{now_str}
            </p>
        </body>
        </html>
        """

            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 明确指定QQ邮箱的SMTP服务器和端口
            server = smtplib.SMTP_SSL('smtp.qq.com', 465)
            # 关闭调试模式，QQ邮箱可能对过于详细的日志有反应
            server.set_debuglevel(False)
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, [to_email], msg.as_string())
            server.quit()

            return True
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False


class DataEncryptUtils:
    def __init__(self):
        self.aes_gcm = AESGCM((b"Guessergdygf!@#sdgygyu1!27637223"))

    def data_encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aes_gcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    def data_decrypt(self, data: bytes) -> bytes:
        nonce = data[:12]
        ciphertext = self.aes_gcm.decrypt(nonce, data[12:], None)
        return ciphertext


@dataclass
class UserInfo:
    username: Optional[str] = None
    password: Optional[str] = None
    email_sender: Optional[str] = None
    email_password: Optional[str] = None
    email_to: Optional[str] = None

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "email_sender": self.email_sender,
            "email_password": self.email_password,
            "email_to": self.email_to
        }

    def to_bytes(self):
        return json.dumps(self.to_dict()).encode("utf-8")

    def dict_to_user_info(self, user_info_dict):
        self.username = user_info_dict.get("username",None)
        self.password = user_info_dict.get("password",None)
        self.email_sender = user_info_dict.get("email_sender",None)
        self.email_password = user_info_dict.get("email_password",None)
        self.email_to = user_info_dict.get("email_to",None)
        return self

    def change_username(self, new_username):
        self.username = new_username
        return self

    def change_password(self, new_password):
        self.password = new_password
        return self

    def change_email_sender(self, new_email_sender):
        self.email_sender = new_email_sender
        return self

    def change_email_password(self, new_email_password):
        self.email_password = new_email_password
        return self

    def change_email_to(self, new_email_to):
        self.email_to = new_email_to
        return self


class UserInfoManager:
    def __init__(self):
        self.user_info = UserInfo()
        self.root_path = os.path.join(real_path(),"user")
        self.lock = threading.Lock()
        self.data_encrypt = DataEncryptUtils()

        if not os.path.exists(self.root_path):
            os.mkdir(self.root_path)

        self.init_user_info()

    def read(self)->UserInfo|None:
        if not os.path.exists(os.path.join(self.root_path,"user_info")):
            return None
        with open(os.path.join(self.root_path,"user_info"), "rb") as f:
            data = self.data_encrypt.data_decrypt(f.read())
            return UserInfo().dict_to_user_info(json.loads(data))

    def write(self, user_info: UserInfo):
        if user_info.username is None:
            return False
        with open(os.path.join(self.root_path,"user_info"), "wb") as f:
            f.write(self.data_encrypt.data_encrypt(user_info.to_bytes()))
            logging.info("用户数据已存盘")
            return True

    def is_userinfo_valid(self) -> bool:
        return bool(self.user_info.username and self.user_info.password)

    def init_user_info(self):
        user_info = self.read()
        if user_info is None:
            return False
        with self.lock:
            self.user_info = user_info
        return True

    def get_user_info(self)->UserInfo:
        with self.lock:
            return self.user_info

    def update_user_info(self, user_info: UserInfo):
        with self.lock:
            self.user_info = user_info
            self.write(user_info)

    def change_user_info(self, username=None, password=None, email_sender=None, email_password=None, email_to=None):
        with self.lock:
            if username:
                self.user_info.change_username(username)
            if password:
                self.user_info.change_password(password)
            if email_sender:
                self.user_info.change_email_sender(email_sender)
            if email_password:
                self.user_info.change_email_password(email_password)
            if email_to:
                self.user_info.change_email_to(email_to)
            self.write(self.user_info)

