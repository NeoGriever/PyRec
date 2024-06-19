import shutil
import win32api
import win32con
import sys


information_gettrace = getattr(sys, 'gettrace', None)

is_in_debug_mode = False

if information_gettrace is not None:
    is_in_debug_mode = True


def format_time(seconds, show_millis=True):
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    hrs, secs = divmod(seconds, 3600)
    minutes, secs = divmod(secs, 60)
    if show_millis:
        return f"{int(hrs):02}:{int(minutes):02}:{int(secs):02}.{millis:03}"
    else:
        return f"{int(hrs):02}:{int(minutes):02}:{int(secs):02}"


def max_w() -> int:
    columns, _ = shutil.get_terminal_size()
    return columns


def get_monitor_info() -> []:
    monitors = []
    device_number = 0
    while True:
        try:
            monitor = win32api.EnumDisplayDevices(None, device_number)
            if not monitor.DeviceName:
                break
            settings = win32api.EnumDisplaySettings(monitor.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
            monitors.append({
                'Index': device_number + 1,
                'DeviceName': monitor.DeviceName,
                'DeviceString': monitor.DeviceString,
                'Position': (settings.Position_x, settings.Position_y),
                'Resolution': (settings.PelsWidth, settings.PelsHeight)
            })
            device_number += 1
        except Exception as e:
            break
    return monitors


class ANSICodes:
    class TextColor:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        yellow = '\033[33m'
        blue = '\033[34m'
        magenta = '\033[35m'
        cyan = '\033[36m'
        white = '\033[37m'
        dark_grey = '\033[90m'
        light_red = '\033[91m'
        light_green = '\033[92m'
        light_yellow = '\033[93m'
        light_blue = '\033[94m'
        light_magenta = '\033[95m'
        light_cyan = '\033[96m'
        light_white = '\033[97m'
        reset = '\033[39m'

    class BgColor:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        yellow = '\033[43m'
        blue = '\033[44m'
        magenta = '\033[45m'
        cyan = '\033[46m'
        white = '\033[47m'
        light_grey = '\033[100m'
        light_red = '\033[101m'
        light_green = '\033[102m'
        light_yellow = '\033[103m'
        light_blue = '\033[104m'
        light_magenta = '\033[105m'
        light_cyan = '\033[106m'
        light_white = '\033[107m'
        reset = '\033[49m'

    class Style:
        italic = '\033[3m'
        underline = '\033[4m'

    resetColors = '\033[39m\033[49m'
    resetAll = '\033[0m'


ansiCodes = ANSICodes()
