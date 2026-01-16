# -*- encoding: utf-8 -*-
# 外部变量/注释开始
# 外部变量/注释结束
"""
@File    :   server.py    
@Author  :   Guesser
@Modify Time      @Version    @Description
------------      --------    -----------
2025/11/17 13:28    1.0         None
"""
from timetable import GuesserCdutetcAuto
from flask import request, send_from_directory, blueprints
from date_parser import FullDateParser
from common import catch_exceptions, Response

app = blueprints.Blueprint('timetable', __name__)
timetable = GuesserCdutetcAuto()
timetable.run()
fullDateParser = FullDateParser()


def process_list_to_str(items: list, msg:str = None):
    result = msg if msg else "当前"
    if not items or len(items) == 0:
        return result + "无课"
    result += f"共有{len(items)}节课。\n"
    for item in items:
        result += "第{}到{}节课，{}，在【{}】教室。\n".format(item["sequence"][0],item["sequence"][-1],
                                                         item["name"],
                                                         item["classroom"])
    return result


@app.route('/')
def index():
    return send_from_directory("templates", "index.html")


@app.route('/timetable', methods=['GET'])
@catch_exceptions
def timetable_():
    return Response.ok(data=timetable.get_everyday_class())


@app.route("/today_class", methods=['GET'])
@catch_exceptions
def today_class():
    is_apple = request.args.get("apple",False)
    success, result = timetable.get_today_class()
    if not success:
        return Response.fail()
    if is_apple:
        return Response.ok(data=process_list_to_str(result, "今日"))
    return Response.ok(data=result)


@app.route("/refresh_timetable", methods=['GET'])
@catch_exceptions
def refresh_timetable():
    try:
        return Response.ok(data=timetable.refresh_timetable())
    except Exception:
        return Response.fail()


@app.route("/get_class_after_days", methods=['GET'])
@catch_exceptions
def get_class_after_days():
    params = request.args
    success, result = timetable.get_class_after_days(int(params['days']))
    if not success:
        return Response.fail()
    if params.get("apple",False):
        return Response.ok(data=process_list_to_str(result, f"{params['days']}天后"))
    return Response.ok(data=result)


@app.route("/get_str_date_class", methods=['GET'])
@catch_exceptions
def get_str_date_class():
    params = request.args
    success, result = timetable.get_str_date_class(params['date'])
    if not success:
        return Response.fail()
    if params.get("apple",False):
        return Response.ok(data=process_list_to_str(result, params['date']))
    return Response.ok(data=result)


@app.route("/get_now_class", methods=['GET'])
@catch_exceptions
def get_now_class():
    success, result = timetable.get_now_class()
    if not success:
        return Response.fail()
    if request.args.get("apple",False):
        return Response.ok(data=process_list_to_str(result, "当前"))
    return Response.ok(data=result)


@app.route("/get_class_by_text", methods=['GET'])
@catch_exceptions
def get_class_by_text():
    text = request.args.get("text","")
    success, type_, value, msg = fullDateParser.parse(text)
    if not success:
        return Response.fail(msg)
    if type_ == "date":
        success, result = timetable.get_str_date_class(value)
        if not success:
            return Response.fail()
        return Response.ok(data=process_list_to_str(result, f"【{value}】"))
    elif type_ == "days":
        if not success:
            return Response.fail()
        success, result = timetable.get_class_after_days(value)
        return Response.ok(data=process_list_to_str(result,
                                                                          f"{'明' if value == 1 else value}天后"))
    elif type_ == "now":
        success, result = timetable.get_now_class()
        if not success:
            return Response.fail()
        return Response.ok(data=process_list_to_str(result,"现在"))
    else:
        return Response.fail("未知异常,请联系开发者")

