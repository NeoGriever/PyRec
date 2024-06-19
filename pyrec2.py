import json
import time
import datetime
import threading
from pynput import mouse, keyboard
from collections import deque
from pathlib import Path
from libs.shorts import get_monitor_info

recording = False
start_time = None
data = deque()
buffer_size = 3000
shard_counter = 0
stop_event = threading.Event()
mouse_buttons = {"left": 0, "right": 0, "middle": 0}
keys_status = {"b": 0, "e": 0}
mouse_position = {"monitor": None, "pos": [0, 0], "res": [0, 0], "rel": [0, 0]}
target_monitor = None
monitor_info = []
start_time_string = None

mouse_listener = None
keyboard_listener = None
key_listener = None

def whereOnScreen(x, y):
    for monitor in monitor_info:
        pos_x, pos_y = monitor['Position']
        width, height = monitor['Resolution']
        if pos_x <= x < pos_x + width and pos_y <= y < pos_y + height:
            relative_x = x - pos_x
            relative_y = y - pos_y
            return {
                'monitor': monitor['Index'],
                'pos': [pos_x, pos_y],
                'res': [width, height],
                'rel': [relative_x, relative_y]
            }
    return None
def start_recording():
    global recording, start_time, data, shard_counter, mouse_position, target_monitor, start_time_string
    start_time_string = datetime.datetime.now().strftime("%m-%d-%y-%H-%M")
    recording = True
    start_time = time.time()
    data = deque()
    shard_counter = 0
    print("Recording started.")
    print("Press F9 to stop recording")

    # Initial mouse position capture
    mouse_controller = mouse.Controller()
    mouse_position = whereOnScreen(mouse_controller.position[0], mouse_controller.position[1])
    target_monitor = mouse_position['monitor']
    record_event()
def stop_recording():
    global recording, start_time, mouse_listener, keyboard_listener, key_listener
    if time.time() - start_time > 1:
        recording = False
        mouse_listener.stop()
        keyboard_listener.stop()
        key_listener.stop()
        save_shard()
        print("Recording stopped.")
        stop_event.set()
        exit(0)
    else:
        print(f"Stop-Command ignored. {time.time() - start_time}")
def save_shard():
    global shard_counter, data
    path = Path(f"shards/{start_time_string}/")
    path.mkdir(parents=True, exist_ok=True)
    filename = path / f"{shard_counter:08d}.json"
    with open(filename, "w") as f:
        json.dump(list(data), f, separators=(',', ':'))
    data.clear()
    shard_counter += 1
    print(f"Shard saved to {filename}.")

def on_move(x, y):
    global mouse_position
    pos_info = whereOnScreen(x, y)
    if pos_info and pos_info['monitor'] == target_monitor:
        mouse_position = pos_info
        record_event()
def on_click(x, y, button, pressed):
    global mouse_position
    pos_info = whereOnScreen(x, y)
    if pos_info and pos_info['monitor'] == target_monitor:
        if button == mouse.Button.left:
            mouse_buttons["left"] = 1 if pressed else 0
        elif button == mouse.Button.right:
            mouse_buttons["right"] = 1 if pressed else 0
        elif button == mouse.Button.middle:
            mouse_buttons["middle"] = 1 if pressed else 0
        mouse_position = pos_info
        record_event()
def on_press(key):
    try:
        if key.char == 'b':
            keys_status["b"] = 1
        elif key.char == 'e':
            keys_status["e"] = 1
    except AttributeError:
        pass
    record_event()
def on_release(key):
    try:
        if key.char == 'b':
            keys_status["b"] = 0
        elif key.char == 'e':
            keys_status["e"] = 0
    except AttributeError:
        pass
    record_event()

def on_key_press(key):
    if key == keyboard.Key.f9:
        if not recording:
            start_recording()
        else:
            stop_recording()

def record_event():
    if not recording:
        return
    if not mouse_position:
        return

    timestamp = int((time.time() - start_time) * 1_000_000)  # Timestamp in microseconds
    entry = {
        "time": f"{timestamp:032d}",
        "mouse": {
            "buttons": mouse_buttons.copy(),
            "position": mouse_position
        },
        "keys": keys_status.copy()
    }
    data.append(entry)
    if len(data) >= buffer_size:
        save_shard()

def main():
    global monitor_info, mouse_listener, keyboard_listener, key_listener
    monitor_info = get_monitor_info()

    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    key_listener = keyboard.Listener(on_press=on_key_press)

    mouse_listener.start()
    keyboard_listener.start()
    key_listener.start()

    print("Press F9 to start recording")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        if recording:
            stop_recording()

if __name__ == "__main__":
    main()
