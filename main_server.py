# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   main_server.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2026/1/16 18:17    1.0         None
"""
import os.path

from flask import Flask, request, send_from_directory
from data_messenger import USER_INFO_MANAGER, user_login
from common import Response,catch_exceptions, real_path
import timetable_bp
import score_query_bp


app = Flask(__name__)
app.register_blueprint(timetable_bp.app,url_prefix='/timetable')
app.register_blueprint(score_query_bp.bq,url_prefix='/score')


@app.route('/')
def index():
    return send_from_directory(os.path.join(real_path(), 'templates'),'index.html')


@app.route("/static/<path:path>")
def static_(path):
    return send_from_directory(os.path.join(real_path(), 'static'),path)


@app.route('/api/is_has_user_info', methods=['GET'])
@catch_exceptions
def is_has_user_info():
    return Response.ok(data=USER_INFO_MANAGER.is_userinfo_valid())


@app.route('/api/login', methods=['POST', "GET"])
@catch_exceptions
def login():
    if request.method == "POST":
        data = request.json
        username = data.get('username',None)
        password = data.get('password',None)
        if username is None or password is None:
            return Response.fail("用户名或密码异常")
        login_result = user_login(username, password)
        if login_result.login_status:
            return Response.ok()
        else:
            return Response.fail("登录失败,请检查账号密码是否正确")

    if request.method == "GET":
        if not USER_INFO_MANAGER.is_userinfo_valid():
            return Response.fail("本地未有账号密码记录")

        if user_login().login_status:
            return Response.ok()
        else:
            return Response.fail("登录异常,可能是本地账号密码不正确或网络异常")

    return Response.fail("不支持的请求方式")


@app.route('/api/change_user_info', methods=['POST'])
@catch_exceptions
def change_user_info():
    data = request.json
    username = data.get('username',None)
    password = data.get('password',None)
    email_sender = data.get('email_sender',None)
    email_password = data.get('email_password',None)
    email_to = data.get('email_to',None)
    USER_INFO_MANAGER.change_user_info(username, password, email_sender, email_password, email_to)
    return Response.ok()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
