import os
import json
import time
import math
import argparse
from typing import List, Any

import threading
from pathlib import Path
from pynput import keyboard, mouse
from libs.shorts import ansiCodes, format_time, get_monitor_info, max_w, is_in_debug_mode

os.system("color")

ts = max_w()

scaling_factor = 1.0
maxletters: int = min(ts, 78)

current_duration = 0
start_time = 0
current_active: List = [False, False, False, False, False]
current_step = 0
current_steps = 1
current_time_offset = 0


def load_entries(shard_file):
    with open(shard_file, 'r') as f:
        return json.load(f)


def load_shards(shard_dir: Path) -> ():
    shard_entries: list[Any] = []
    for filename in sorted(os.listdir(shard_dir)):
        if filename.endswith('.json'):
            shard_entries.extend(load_entries(os.path.join(shard_dir, filename)))
    return tuple(shard_entries)


def set_mouse_position(entry, monitors):
    monitor = monitors[entry['mouse']['position']['monitor'] - 1]
    x = monitor['Position'][0] + entry['mouse']['position']['rel'][0]
    y = monitor['Position'][1] + entry['mouse']['position']['rel'][1]
    mouse_con.position = (x, y)


def execute_event(current_entry, prev_entry):
    set_mouse_position(current_entry, monitor_info)

    mousetriggers = [0, 0, 0]
    if prev_entry:
        for i, button in enumerate(['left', 'middle', 'right']):
            if not prev_entry['mouse']['buttons'][button] and current_entry['mouse']['buttons'][button]:
                mousetriggers[i] = 1
            elif prev_entry['mouse']['buttons'][button] and not current_entry['mouse']['buttons'][button]:
                mousetriggers[i] = -1

    for i, button in enumerate([mouse.Button.left, mouse.Button.middle, mouse.Button.right]):
        if mousetriggers[i] == 1:
            mouse_con.press(button)
        elif mousetriggers[i] == -1:
            mouse_con.release(button)

    keytriggers = [0, 0, 0]
    keys = ['b', 'e']
    if prev_entry:
        for i, key in enumerate(keys):
            if not prev_entry['keys'][key] and current_entry['keys'][key]:
                keytriggers[i] = 1
            elif prev_entry['keys'][key] and not current_entry['keys'][key]:
                keytriggers[i] = -1

    for i, key in enumerate(['b', 'e']):
        if keytriggers[i] == 1:
            if key == 'b':
                keyboard_con.press('b')
            elif key == 'e':
                keyboard_con.press('e')
        elif keytriggers[i] == -1:
            if key == 'b':
                keyboard_con.release('b')
            elif key == 'e':
                keyboard_con.release('e')


def display_total_duration(active_entries: List):
    if not active_entries:
        print("No entries found.")
        return
    original_duration = int(active_entries[-1]['time']) / 1_000_000  # in seconds
    scaled_duration = original_duration * scaling_factor
    original_duration_str = format_time(original_duration, True)
    scaled_duration_str = format_time(scaled_duration, True)
    return [
        original_duration,
        scaled_duration,
        original_duration_str,
        scaled_duration_str,
    ]


def display_progress():
    global current_duration, start_time, current_active, current_step, current_steps, current_time_offset, maxletters

    step_len = len(str(current_steps))

    maxletters = maxletters - 24 + (step_len * 2)

    update_interval = 0.1
    breaks = "\033[F" * 3

    colors = [
        [ansiCodes.TextColor.green, ansiCodes.BgColor.green, ansiCodes.TextColor.dark_grey, ansiCodes.BgColor.black],
        [ansiCodes.TextColor.light_blue, ansiCodes.BgColor.light_blue, ansiCodes.TextColor.blue,
         ansiCodes.BgColor.black],
    ]

    print(f"")
    own_thread = threading.current_thread()
    while current_step < current_steps:
        if not getattr(own_thread, "active", True):
            break
        current_time_left = current_duration - current_time_offset
        str_rest = format_time(max(0, current_time_left), True)

        progress = min(maxletters, int(math.ceil((current_time_offset / current_duration) * maxletters)))
        progress_steps = min(maxletters, int(math.ceil((current_step / current_steps) * maxletters)))
        ca = ansiCodes.TextColor.green
        cd = ansiCodes.TextColor.dark_grey
        rs = ansiCodes.resetAll

        print(f"", end=breaks)
        print(
            f"{colors[0][0]}{colors[0][1]}{f'█' * progress}" +
            f"{colors[0][2]}{colors[0][3]}{'▒' * (maxletters - progress)}{rs}")
        print(
            f"{colors[1][0]}{colors[1][1]}{f'█' * progress_steps}" +
            f"{colors[1][2]}{colors[1][3]}{'▒' * (maxletters - progress_steps)}{rs}")
        print(
            f"" +
            f"{ca}{str_rest}" +
            f"{rs} | " +
            f"{ca}{current_step:>{step_len}} / {current_steps:>{step_len}}" +
            f"{rs} | " +
            f"{cd if not current_active[0] else ca}[left] " +
            f"{ca if current_active[1] else cd}[middle] " +
            f"{ca if current_active[2] else cd}[right]" +
            f"{rs} | " +
            f"{ca if current_active[3] else cd}[B] " +
            f"{ca if current_active[4] else cd}[E]" +
            f"{rs}"
        )
        time.sleep(update_interval)
        current_time_offset += update_interval
    own_thread.active = False


def play_back(active_entries: List, ref_display_thread: threading.Thread):
    global current_duration, start_time, current_active, current_step, current_steps, current_time_offset
    activity_thread_started = False
    total_duration = display_total_duration(active_entries)
    current_duration = total_duration[1]
    start_time = time.time()
    current_active = [False, False, False, False, False]
    current_steps = len(active_entries)
    current_step = 0
    own_thread = threading.current_thread()
    for i, current_entry in enumerate(active_entries):
        if not getattr(own_thread, "active", True):
            break
        prev_entry = active_entries[i - 1] if i > 0 else None
        next_entry = active_entries[i + 1] if i < len(active_entries) - 1 else None

        sleep_time = 0
        sleep_start_time = time.time()
        if next_entry:
            difference = int(next_entry['time']) - int(current_entry['time'])
            sleep_time = difference / 1_000_000 * scaling_factor

        current_step = current_step + 1

        current_time_offset = int(current_entry["time"]) / 1_000_000

        keys = ['b', 'e']
        if prev_entry:
            for iterator_index_1, key in enumerate(keys):
                if not prev_entry['keys'][key] and current_entry['keys'][key]:
                    current_active[iterator_index_1 + 3] = True
                elif prev_entry['keys'][key] and not current_entry['keys'][key]:
                    current_active[iterator_index_1 + 3] = False
        if prev_entry:
            for iterator_index_2, button in enumerate(['left', 'middle', 'right']):
                if not prev_entry['mouse']['buttons'][button] and current_entry['mouse']['buttons'][button]:
                    current_active[iterator_index_2] = True
                elif prev_entry['mouse']['buttons'][button] and not current_entry['mouse']['buttons'][button]:
                    current_active[iterator_index_2] = False

        execute_event(current_entry, prev_entry)

        if not activity_thread_started:
            activity_thread_started = True
            ref_display_thread.start()

        if next_entry:
            sleep_time = sleep_time - (time.time() - sleep_start_time)
            if sleep_time >= 0.00001:
                time.sleep(sleep_time)
    own_thread.active = False


def stop_playback():
    global key_listener, display_thread, display_thread, \
        current_duration, start_time, current_active, \
        current_step, current_steps, current_time_offset, \
        maxletters
    step_len = len(str(current_steps))
    breaks = "\033[F" * 3

    key_listener.stop()
    display_thread.active = False
    playback_thread.active = False

    colors = [
        [ansiCodes.TextColor.green, ansiCodes.BgColor.green, ansiCodes.TextColor.black, ansiCodes.BgColor.green],
        [ansiCodes.TextColor.light_blue, ansiCodes.BgColor.light_blue, ansiCodes.TextColor.dark_grey,
         ansiCodes.BgColor.blue],
    ]

    current_time_left = current_duration - current_time_offset
    progress = min(maxletters, int(math.ceil((current_time_offset / current_duration) * maxletters)))
    progress_steps = min(maxletters, int(math.ceil((current_step / current_steps) * maxletters)))
    str_rest = format_time(max(0, current_time_left), True)
    print(f"", end=breaks)
    print(
        f"{colors[0][0]}{colors[0][1]}{f'█' * progress}" +
        f"{colors[0][2]}{colors[0][3]}{'▒' * (maxletters - progress)}{ansiCodes.resetAll}"
    )
    print(
        f"{colors[1][0]}{colors[1][1]}{f'█' * progress_steps}" +
        f"{colors[1][2]}{colors[1][3]}{'▒' * (maxletters - progress_steps)}{ansiCodes.resetAll}"
    )
    print(
        f"{ansiCodes.TextColor.green}{str_rest}{ansiCodes.resetAll} | " +
        f"{ansiCodes.TextColor.green}{current_step:>{step_len}} / {current_steps:>{step_len}}{ansiCodes.resetAll} | " +
        f"{ansiCodes.TextColor.dark_grey}[left] [middle] [right]{ansiCodes.resetAll} | " +
        f"{ansiCodes.TextColor.dark_grey}[B] [E]{ansiCodes.resetAll}"
    )


def on_key_press(key):
    if key == keyboard.Key.f10:
        stop_playback()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyPlay V2")
    parser.add_argument('--script', type=str, help='(optional) Defines the script to load')
    parser.add_argument('--speed', type=float, help='(optional) Defines the play speed of the script')
    args = parser.parse_args()

    shard_directory = None
    if args.script:
        shard_directory = Path(f"shards") / Path(args.script)
        pass
    else:
        for subdirectory in Path(f"shards").glob(f"*.json"):
            shard_directory = subdirectory
            break

    if shard_directory is None:
        print(f"No Project to play found")
        exit(0)
    print(f"Using file \"{shard_directory}\"")

    scaling_factor = 1.0

    if args.speed:
        scaling_factor = float(args.speed)

    monitor_info = get_monitor_info()
    mouse_con = mouse.Controller()
    keyboard_con = keyboard.Controller()
    # entries = load_shards(shard_directory)
    entries = load_entries(f"{shard_directory}")

    duration_data = display_total_duration(entries)
    print(f"Original duration:       {duration_data[2]}")
    print(f"Average scaled duration: {duration_data[3]}")

    start_time_pause = time.time()

    while time.time() - start_time_pause < 5:
        print(f"Starting in {f"{(5 - (time.time() - start_time_pause)):.2f}":>4} Seconds", end="\r")
        time.sleep(0.01)

    if is_in_debug_mode:
        print(f"Debug Kill before Starting")
        exit(0)
    else:
        print(f"")

    print(f"Script started ...")
    print(f"")
    print(f"")

    key_listener = keyboard.Listener(on_press=on_key_press)
    display_thread = threading.Thread(target=display_progress)
    playback_thread = threading.Thread(target=play_back, args=(entries, display_thread,))
    playback_thread.active = True
    display_thread.active = True
    key_listener.start()
    playback_thread.start()

    try:
        while playback_thread.active and display_thread.active:
            time.sleep(0.1)
        stop_playback()
    except KeyboardInterrupt:
        stop_playback()
