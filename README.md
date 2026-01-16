# cdutetc
成理工程教务系统自动登录，课表处理为 API 以便接入其他提醒系统。支持历史成绩查询、学分统计、成绩实时更新与邮件通知，以及重修缴费统计。

## 功能概览
- 自动登录教务系统并保存账号信息。
- 课表查询：完整课表、今日课程、当前课程、指定日期与自然语言查询。
- 成绩查询：历史成绩、本学期成绩、学分统计、重修缴费统计。
- 邮件通知：支持启用/关闭成绩邮件通知。
- 前端页面：现代设计风格的统一操作面板，并在首次打开时弹出免责声明。

## 启动方式
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动服务：
   ```bash
   python main_server.py
   ```
3. 访问前端页面：
   - `http://localhost:5000/timetable/`（前端入口）

## 前端说明
前端页面覆盖所有后端已实现的功能，提供统一的操作按钮与结果展示区。首次打开页面会提示免责声明，确认后才可继续使用。

## API 快速参考
### 账号/基础功能
- `GET /api/is_has_user_info`
- `POST /api/login`
- `GET /api/login`
- `POST /api/change_user_info`

### 课表接口（前缀 `/timetable`）
- `GET /timetable`
- `GET /today_class`
- `GET /refresh_timetable`
- `GET /get_class_after_days?days=2`
- `GET /get_str_date_class?date=2026-01-16`
- `GET /get_now_class`
- `GET /get_class_by_text?text=明天`

### 成绩接口（前缀 `/score`）
- `GET /init`
- `GET /all_score`
- `GET /enable_email`
- `GET /disable_email`
- `GET /query_retake_total_paid`
- `GET /query_this_semester`
- `GET /update`
- `GET /accumulate_history_credits`
