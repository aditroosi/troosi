import os
import time
import audio_to_text
import image_text_prompting
import text_to_csv_process
import video_to_audio_conversion
import video_to_image_conversion
from datetime import datetime

# === Replace with your table config manually ===
TABLE_NAME = "sample_table"
TABLE_DICT = {
    "input_video_folder": "input_videos",
    "table_name": TABLE_NAME,
    "frame_interval_in_seconds": 1.5  # <-- use float or int seconds
}

def trigger_action(table_name):
    print("🚀 SWITCH is ON – performing the action...")
    table_dict = TABLE_DICT
    print(f"Table data: {table_dict}")

    mp4_files = [f for f in os.listdir("input_videos") if f.endswith(".mp4")]

    for mp4_file in mp4_files:
        print("Processing:", mp4_file)
        video_to_audio_conversion.extract_audio_from_input_videos(mp4_file)

        # Modified: Pass seconds instead of frame interval
        video_to_image_conversion.extract_frames_every_n_seconds(mp4_file, float(table_dict["frame_interval_in_seconds"]))

        image_text_prompting.process_folder_and_store_csv(mp4_file.replace(".mp4", ""))
        audio_to_text.transcribe_audio_and_update_file(mp4_file.replace(".mp4", ".mp3"))
        text_to_csv_process.summarize_and_append_to_master_csv(
            frame_csv_path=f"csv_results/{mp4_file.replace('.mp4', '_frame_level.csv')}",
            audio_csv_path=f"csv_results/{mp4_file.replace('.mp4', '_audio_result.csv')}",
            file_label=mp4_file.replace(".mp4", "")
        )

    print(f"✅ Action completed for table: {table_name}")

if __name__ == "__main__":
    try:
        start = datetime.now()
        print(f"Processing for table: {TABLE_NAME}")
        trigger_action(TABLE_NAME)
        end = datetime.now()
        print(f"⏱️ Time taken: {end - start}")
    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
