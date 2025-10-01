import os
import csv
from video_length_calculation import get_video_length  
from mysql_process import generate_prompts_from_mysql

def summarize_and_append_to_master_csv(frame_csv_path, audio_csv_path, file_label, master_csv_path="summary_results.csv"):
    # Step 1: Summarize frame-level CSV
    if not os.path.exists(frame_csv_path):
        print(f"❌ Frame-level file not found: {frame_csv_path}")
        return
    with open(frame_csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        frame_header = reader[0][1:]  # skip 'frame'
        rows = reader[1:]

    prompts = generate_prompts_from_mysql()
    key_time_lookup = {p['key']: int(p['time']) for p in prompts}
    #print(f"Key time lookup: {key_time_lookup}")
    frame_summary = [0] * len(frame_header)
    #print(f"Processing {len(frame_header)} keys for file label '{file_label}'")
    #print(rows)
    for i, key in enumerate(frame_header):
        check_time = key_time_lookup.get(key, 0)
        row_limit = len(rows) if check_time == 0 else min(check_time, len(rows))
        values = [int(row[i + 1].strip()) for row in rows[:row_limit] if row[i + 1].strip().isdigit()]

        if "__min" in key:
            frame_summary[i] = 1 if any(val == 1 for val in values) else 0
        elif "__max" in key:
            frame_summary[i] = 1 if values and max(values) == 1 else 0
        elif "__avg" in key:
            frame_summary[i] = (sum(values) / len(values))*100 if values else 0
        elif "__all" in key:
            frame_summary[i] = 1 if all(val == 1 for val in values) else 0            
        else:
            for row in rows[:row_limit]:
                if row[i + 1].strip() == "1":  # +1 to skip frame number
                    frame_summary[i] = 1
                    break


        
    # Step 2: Load audio result CSV
    if not os.path.exists(audio_csv_path):
        print(f"❌ Audio result file not found: {audio_csv_path}")
        return
    with open(audio_csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        audio_header = reader[0][1:]  # skip 'audio_file'
        audio_row = reader[1][1:]     # skip audio_file name

    # Step 3: Combine headers and values
    video_path = os.path.join("input_videos", file_label + ".mp4")
    video_length = get_video_length(video_path) if os.path.exists(video_path) else 0.0
    combined_header = ["file_name"] + frame_header + audio_header + ["video_length"]
    combined_row = [file_label] + frame_summary + audio_row + [video_length]

    # Step 4: Append to master CSV or create it
    file_exists = os.path.exists(master_csv_path)
    with open(master_csv_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(combined_header)
        writer.writerow(combined_row)

    print(f"✅ Summary for '{file_label}' appended to: {master_csv_path}")
# Example usage
if __name__ == "__main__":
    summarize_and_append_to_master_csv(
        frame_csv_path="csv_results/1_frame_level.csv",
        audio_csv_path="csv_results/1_audio_result.csv",
        file_label="1"
    )
