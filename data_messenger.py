# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   main.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2026/1/16 18:14    1.0         None
"""
import threading
from login import GuesserLogin, LoginResult
import common
USER_INFO_MANAGER = common.UserInfoManager()


class DataMessenger:
    def __init__(self):
        self.LOGIN_RESULT = None
        self.lock = threading.Lock()

    def update_login_result(self, login_result):
        with self.lock:
            self.LOGIN_RESULT = login_result

    def get_login_result(self)->LoginResult|None:
        with self.lock:
            return self.LOGIN_RESULT

    @staticmethod
    def get_user_info():
        return USER_INFO_MANAGER.get_user_info()


DATA_MESSENGER = DataMessenger()


def user_login(username=None, password=None)->LoginResult|None:
    if username and password:
        login_result = GuesserLogin(username=username, password=password).run()
        if login_result.login_status:
            DATA_MESSENGER.update_login_result(login_result)
            USER_INFO_MANAGER.change_user_info(username=username, password=password)
        return login_result
    if not USER_INFO_MANAGER.is_userinfo_valid():
        return None
    user_info = USER_INFO_MANAGER.get_user_info()
    login_result = GuesserLogin(username=user_info.username, password=user_info.password).run()
    DATA_MESSENGER.update_login_result(login_result)
    return login_result
