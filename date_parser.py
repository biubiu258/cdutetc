import re
from datetime import datetime, timedelta


class FullDateParser:
    def __init__(self):
        self.now = datetime.now()

        self.chinese_number_map = {
            "一": 1,
            "二": 2,
            "两": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10
        }

        self.week_map = {
            "一": 0,
            "二": 1,
            "三": 2,
            "四": 3,
            "五": 4,
            "六": 5,
            "七": 6,
            "日": 6,
            "天": 6,
        }

    def ok(self, type_, value):
        return (True, type_, value, "")

    def err(self, msg):
        return (False, "error", None, msg)

    def parse(self, text: str):
        text = text.strip()
        if re.search(r"(眼下|现阶段|现在|当下|此刻|当前)", text):
            return self.ok("now", 0)
        # 1. 明天、后天、大后天
        rel_map = {
            "明天": 1,
            "后天": 2,
            "大后天": 3,
        }
        for k, v in rel_map.items():
            if k in text:
                return self.ok("days", v)

        # 2. n天后
        m = re.search(r"([两一二三四五六七八九十\d]+)\s*天(后|之后|以后)?", text)
        if m:
            num_text = m.group(1)

            if num_text.isdigit():
                days = int(num_text)
            else:
                days = self.chinese_number_map.get(num_text)
                if days is None:
                    return self.err("无法识别的中文数字天数")

            return self.ok("days", days)

        # 3. 本周几 / 下周几 / 下下周几
        m = re.search(r"(本周|下周|下下周)?(周|星期)([一二三四五六七日天])", text)
        if m:
            prefix = m.group(1)
            weekday_char = m.group(3)
            target_weekday = self.week_map[weekday_char]

            base = self.now
            if prefix == "下周":
                base += timedelta(weeks=1)
            elif prefix == "下下周":
                base += timedelta(weeks=2)

            today_weekday = base.weekday()
            offset = (target_weekday - today_weekday) % 7
            if offset == 0:
                offset = 7  # 避免今天

            d = base + timedelta(days=offset)
            return self.ok("date", d.strftime("%Y-%m-%d"))

        # 4. 几月几号（无年份）
        m = re.search(r"(\d{1,2})月(\d{1,2})[号日]?", text)
        if m and "年" not in text:
            month = int(m.group(1))
            day = int(m.group(2))
            year = self.now.year

            try:
                d = datetime(year, month, day)
            except:
                return self.err("日期无效")

            if d < self.now:
                year += 1
                d = datetime(year, month, day)

            return self.ok("date", d.strftime("%Y-%m-%d"))

        # 5. YYYY年MM月DD日
        m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})[号日]?", text)
        if m:
            year, month, day = map(int, m.groups())
            try:
                d = datetime(year, month, day)
            except:
                return self.err("日期无效")

            return self.ok("date", d.strftime("%Y-%m-%d"))

        # 6. 明年/后年 + 几月几号
        m = re.search(r"(明年|后年)(\d{1,2})月(\d{1,2})[号日]?", text)
        if m:
            prefix = m.group(1)
            year_offset = 1 if prefix == "明年" else 2
            year = self.now.year + year_offset
            month = int(m.group(2))
            day = int(m.group(3))

            try:
                d = datetime(year, month, day)
            except:
                return self.err("日期无效")

            return self.ok("date", d.strftime("%Y-%m-%d"))

        # 7. 这个月几号
        m = re.search(r"(这个月|本月)(\d{1,2})[号日]?", text)
        if m:
            day = int(m.group(2))
            year = self.now.year
            month = self.now.month

            try:
                d = datetime(year, month, day)
            except:
                return self.err("日期无效")

            if d < self.now:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                d = datetime(year, month, day)

            return self.ok("date", d.strftime("%Y-%m-%d"))

        # 8. 下个月几号
        m = re.search(r"下个月(\d{1,2})[号日]?", text)
        if m:
            day = int(m.group(1))
            year = self.now.year
            month = self.now.month + 1
            if month > 12:
                month = 1
                year += 1

            try:
                d = datetime(year, month, day)
            except:
                return self.err("日期无效")

            return self.ok("date", d.strftime("%Y-%m-%d"))

        # 9. 今天
        if "今天" in text:
            return self.ok("date", self.now.strftime("%Y-%m-%d"))

        # 10. 未识别
        return self.err("无法识别日期，请尝试：1天后 / 下周三 / 5月3号 / 2025年1月1号")
