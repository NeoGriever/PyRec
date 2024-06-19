import os
import json

def adjust_timestamps(shard_dir):
    max_offset = 10000  # 10 milliseconds in microseconds
    entries = []
    filenames = sorted([f for f in os.listdir(shard_dir) if f.endswith('.json')])

    # Load all entries from shards
    for filename in filenames:
        with open(os.path.join(shard_dir, filename), 'r') as f:
            entries.extend(json.load(f))

    if not entries:
        print("No entries found.")
        return

    # Determine initial offset adjustment
    initial_time = int(entries[0]['time'])
    offset_adjustment = initial_time - max_offset if initial_time > max_offset else 0

    # Adjust timestamps
    for entry in entries:
        original_time = int(entry['time'])
        new_time = original_time - offset_adjustment
        entry['time'] = f"{new_time:032d}"

    # Save adjusted entries back to shards
    entry_index = 0
    for filename in filenames:
        shard_entries = entries[entry_index:entry_index+len(json.load(open(os.path.join(shard_dir, filename), 'r')))]
        with open(os.path.join(shard_dir, filename), 'w') as f:
            json.dump(shard_entries, f, separators=(',', ':'))
        entry_index += len(shard_entries)

if __name__ == "__main__":
    shard_directory = 'shards'
    adjust_timestamps(shard_directory)
    print("Timestamps adjusted successfully.")
