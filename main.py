import json
import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event


# 读取JSON文件
def load_schedule(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


# 将"7-8节"的节次转换为具体的上课时间
def class_time_to_hours(class_period):
    period_times = {
        '1-2': ('08:00', '09:50'),
        '3-4': ('10:20', '12:10'),
        '5-6': ('14:00', '15:50'),
        '7-8': ('16:20', '18:10'),
        '9-10': ('19:00', '20:50'),
        '9-11': ('19:00', '21:50')
    }
    return period_times.get(class_period)


# 解析kbxx字段中的信息，支持单/双周
def parse_kbxx(kbxx):
    pattern = r'(?P<course_name>.*?)\n\[(?P<teacher>.*?)\]\n\[(?P<class_info>.*?)\]\n\[(?P<week_info>.*?)\]\[(?P<location>.*?)\]\[(?P<time_info>.*?)\]'
    match = re.match(pattern, kbxx)
    if match:
        return match.groupdict()
    else:
        print(f'Error: {kbxx}')
        return None


# 解析key字段中的星期几信息
def parse_key(key):
    pattern = r'xq(?P<day_of_week>\d)_jc\d+'
    match = re.match(pattern, key)
    if match:
        return int(match.group('day_of_week'))
    print(f'Error: {key}')
    return None


# 根据周次和星期几生成课程日期，支持单/双周
def generate_class_date(start_date, week_range, day_of_week):
    # 判断是否有“单”或“双”字样
    is_single_week = "单" in week_range
    is_double_week = "双" in week_range
    week_range = re.sub(r"[单双]", "", week_range)  # 去掉“单”或“双”

    start_week, end_week = map(int, week_range.split('-'))
    class_dates = []

    for week in range(start_week, end_week + 1):
        # 如果是单周，跳过双周
        if is_single_week and week % 2 == 0:
            continue
        # 如果是双周，跳过单周
        if is_double_week and week % 2 != 0:
            continue
        class_date = start_date + timedelta(weeks=week - 1, days=day_of_week - 1)
        class_dates.append(class_date)

    return class_dates


# 将课程信息转化为ICS格式
def create_ics(schedule_data, output_file, start_monday):
    cal = Calendar()
    for item in schedule_data:
        kbxx = item.get('kbxx')
        key = item.get('key')  # 获取key字段
        if kbxx and key:
            parsed_info = parse_kbxx(kbxx)
            day_of_week = parse_key(key)  # 从key字段中解析星期几
            if parsed_info and day_of_week is not None:
                course_name = parsed_info['course_name']
                teacher = parsed_info['teacher']
                week_range = parsed_info['week_info'].replace("周", "")
                location = parsed_info['location']
                time_info = parsed_info['time_info'].replace("节", "")
                class_time = class_time_to_hours(time_info)

                if class_time:
                    start_time, end_time = class_time
                    class_dates = generate_class_date(start_monday, week_range, day_of_week)

                    for class_date in class_dates:
                        event = Event()
                        event.add('summary', course_name)
                        event.add('dtstart',
                                  datetime.combine(class_date, datetime.strptime(start_time, '%H:%M').time()))
                        event.add('dtend', datetime.combine(class_date, datetime.strptime(end_time, '%H:%M').time()))
                        event.add('location', location)
                        event.add('description', f'{course_name} - {teacher}')
                        cal.add_component(event)

    # 将日历写入ICS文件
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())


# 主程序
if __name__ == '__main__':
    schedule_file = 'data.json'  # 你的课表文件路径
    output_file = 'schedule.ics'  # 输出的ICS文件路径
    start_monday = datetime(2025, 2, 17)  # 开学第一周的周一日期
    schedule_data = load_schedule(schedule_file)
    create_ics(schedule_data, output_file, start_monday)
