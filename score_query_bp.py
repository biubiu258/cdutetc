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


@bq.route('/init', methods=['GET'])
@catch_exceptions
def init():
    Query.init()
    return Response.ok()


@bq.route('/all_score', methods=['GET', 'POST'])
@catch_exceptions
def all_score():
    return Response.ok(data=Query.get_all_history())


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
    # items是一个列表，示例数据如下
    '''    {
      "bmpc": "-1",
      "date": "二○二六年一月十五日",
      "dateDigit": "2026年1月15日",
      "dateDigitSeparator": "2026-1-15",
      "day": "15",
      "jfjssj": "2025-10-31 23:59:59",
      "jfkssj": "2025-10-22 00:00:00",
      "jfxnm": "2025",
      "jfxqm": "3",
      "jgpxzd": "1",
      "listnav": "false",
      "localeKey": "zh_CN",
      "month": "1",
      "order_amount": "320.00",
      "order_count": "1",
      "order_id": "ZZJF202404161557585935",
      "order_men": "12300060219",
      "order_name": "高等数学I1",
      "pageTotal": 0,
      "pageable": true,
      "pay_state": "1",
      "pay_time": "2024-04-16 16:00:53",
      "queryModel": {
        "currentPage": 1,
        "currentResult": 0,
        "entityOrField": false,
        "limit": 15,
        "offset": 0,
        "pageNo": 0,
        "pageSize": 15,
        "showCount": 10,
        "sorts": [],
        "totalCount": 0,
        "totalPage": 0,
        "totalResult": 0
      },
      "rangeable": true,
      "row_id": "4",
      "sfqr": "已缴费",
      "sfzfzzt": "0",
      "totalResult": "4",
      "userModel": {
        "monitor": false,
        "roleCount": 0,
        "roleKeys": "",
        "roleValues": "",
        "status": 0,
        "usable": false
      },
      "xm": "名字",
      "xmdm": "200038",
      "xnm": "2023",
      "xnmc": "2023-2024",
      "xqm": "12",
      "xqmc": "2",
      "year": "2026",
      "ywdm": "05",
      "ywmc": "重修选课费",
      "zfywsj_ids": "15BA47B5985EAB91E065000000000001"
    }'''
    return Response.ok(data={'total_retake_paid': total_retake_paid,"items": result})


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
    return Response.ok(data={'total': total, 'failed': failed,"succeeded": succeeded, "total_failed": total_failed})
