import os
import json
import shutil
import argparse
from pathlib import Path
from libs.shorts import ansiCodes, format_time

def load_shards(shard_dir):
    entries = []
    for filename in sorted(os.listdir(shard_dir)):
        if filename.endswith('.json'):
            with open(os.path.join(shard_dir, filename), 'r') as f:
                entries.extend(json.load(f))
    return entries

def adjust_time_intervals(entries, max_interval=1_000_000, lineBefore=""):
    previous_time = 0
    reducedEntries = 0
    original = int(entries[-1]["time"]) / 1_000_000
    total_offset_reduce = 0
    for i in range(len(entries)):
        entries[i]['time'] = int(int(entries[i]['time']) - total_offset_reduce)
        current_time = int(entries[i]['time'])
        if current_time - previous_time > max_interval:
            original_time = current_time
            entries[i]['time'] = int(previous_time + max_interval)
            difference = original_time - (previous_time + max_interval)
            total_offset_reduce += difference
            reducedEntries = reducedEntries + 1

        print(f"", end="\033[F" * 5)
        print(f"BEFORE:                        {format_time(original, True)}")
        print(f"After:                         {format_time(int(int(entries[-1]["time"]) - total_offset_reduce) / 1_000_000, True)}")
        print(f"Amount of cleaned entries: {reducedEntries:>6} of {len(entries):>6}")
        print(f"Checked entries:           {i:>6} of {len(entries):>6}")
        print(f"Workset:        {format_time(int(entries[i]['time']) / 1_000_000)} | {format_time(int(total_offset_reduce) / 1_000_000)}")

        previous_time = int(entries[i]['time'])
    return [entries, reducedEntries]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyMove V2")
    parser.add_argument('--script', type=str, help='(optional) Defines the Script using')
    parser.add_argument('--offset', type=int, help='(optional) Defines the maximum offset')
    args = parser.parse_args()

    seconds = 1

    shard_directory = Path(f"shards")
    if args.script:
        shard_directory = Path(f"shards") / Path(args.script)
        pass
    else:
        for subdirectory in shard_directory.iterdir():
            if subdirectory.is_dir():
                shard_directory = subdirectory
                break
    if args.offset:
        seconds = int(args.offset) / 1_000_000
    else:
        pass

    os.system("color")
    print(f"Before:                        00:00:00.000")
    print(f"After:                         00:00:00.000")
    print(f"Amount of cleaned entries:      0 of      0")
    print(f"Checked entries:                0 of      0")
    print(f"Workset:        00:00:00.000 | 00:00:00.000")

    entries = load_shards(shard_directory)
    root_time = int(entries[-1]["time"])
    beforeSTR = f"{format_time(root_time / 1_000_000, True)}"
    lineBefore = f"Before:                        {beforeSTR}"
    cleaned_entries = adjust_time_intervals(entries, seconds * 1_000_000, lineBefore)

    print(f"", end="\033[F" * 5)
    print(lineBefore)
    print(f"After:                         {format_time(int(cleaned_entries[0][-1]["time"]) / 1_000_000, True)}")
    print(f"Amount of cleaned entries: {cleaned_entries[1]:>6} of {len(entries):>6}")
    print(f"Checked entries:           {len(entries):>6} of {len(entries):>6}")
    print(f"Workset:        {format_time(int(entries[-1]["time"]) / 1_000_000, True)} | {format_time((root_time - int(cleaned_entries[0][-1]["time"])) / 1_000_000, True)}")

    filename = f"{shard_directory}.json"

    with open(filename, "w") as f:
        json.dump(list(cleaned_entries[0]), f, separators=(',', ':'))

    print(f"Saved as {filename}")
