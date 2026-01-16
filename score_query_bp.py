# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   score_query_bp.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2026/1/16 17:19    1.0         None
"""
from score_query import Query
from flask import blueprints
from common import catch_exceptions, Response
from data_messenger import DATA_MESSENGER

bq = blueprints.Blueprint('score_query_bp', __name__)
Query = Query()
INIT_FLAG = False


@bq.route('/init', methods=['GET'])
@catch_exceptions
def init():
    Query.run()
    global INIT_FLAG
    INIT_FLAG = True
    return Response.ok()


@bq.route('/all_score', methods=['GET', 'POST'])
@catch_exceptions
def all_score():
    Response.ok(data=Query.get_all_history())


@bq.route('/enable_email', methods=['GET'])
@catch_exceptions
def enable_email():
    user_info = DATA_MESSENGER.get_user_info()
    if not user_info:
        return Response.fail("用户信息缺失，请先进行邮件设置")
    if user_info.email_to and user_info.email_password and user_info.email_to:
        Query.set_email_user(user_info.email_sender, user_info.email_password, user_info.email_to)
        return Response.ok()
    return Response.fail("邮箱发送者或接收者设置不正确！")


@bq.route('/disable_email', methods=['GET'])
@catch_exceptions
def disable_email():
    Query.set_email_user()
    return Response.ok()


@bq.route('/query_retake_total_paid', methods=['GET'])
@catch_exceptions
def query_retake_total_paid():
    result = Query.query_retake_paid()
    total_retake_paid = Query.process_total_retake_paid(result)
    return Response.ok(data={'total_retake_paid': total_retake_paid,"items": total_retake_paid})


@bq.route('/query_this_semester', methods=['GET'])
@catch_exceptions
def query_this_semester():
    result = Query.get_this_semester()
    return Response.ok(data=result)


@bq.route('/update', methods=['GET'])
@catch_exceptions
def update():
    Query.run()
    return Response.ok()


@bq.route('/accumulate_history_credits', methods=['GET'])
@catch_exceptions
def accumulate_history_credits():
    total, failed, succeeded, total_failed = Query.accumulate_credits()
    return Response.ok(data={'total': total, 'failed': failed,succeeded: succeeded, total_failed: total_failed})
