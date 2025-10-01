# Troosi Media Intelligence Pipeline

## High-level overview
This repository implements an offline pipeline that turns raw marketing videos into structured CSV reports. The workflow orchestrated in [`all_process.py`](all_process.py) performs the following steps:

1. **Video ingestion** – Iterate over every `.mp4` file inside `input_videos/`.
2. **Audio extraction** – Use MoviePy to save an `.mp3` copy for each video (`video_to_audio_conversion.extract_audio_from_input_videos`).
3. **Frame extraction** – Use OpenCV to grab still images every _N_ seconds (`video_to_image_conversion.extract_frames_every_n_seconds`).
4. **Frame analysis** – Send each frame to Groq's multimodal LLM with prompts loaded from `tracking_details.csv` and store yes/no flags per frame (`image_text_prompting.process_folder_and_store_csv`).
5. **Audio transcription & analysis** – Transcribe the `.mp3` with Groq Whisper, run a prompt-based classification, and store a single yes/no row (`audio_to_text.transcribe_audio_and_update_file`).
6. **Summary aggregation** – Merge frame-level + audio-level outputs, compute summary metrics, and append to `summary_results.csv` (`text_to_csv_process.summarize_and_append_to_master_csv`).

Each step is designed to be reusable individually, but the `all_process.trigger_action` function links everything together for batch processing.

## Repository layout
```
input_videos/                # Expected folder for source MP4s (created externally)
audio_files/                 # Generated mp3 files
extracted_frames/            # Per-video subfolders holding extracted frames
csv_results/                 # Per-video frame and audio CSVs
individual_frame_responses/  # Text log of transcriptions and LLM answers
tracking_details.csv         # Prompt catalogue exported from MySQL
summary_results.csv          # Master roll-up (appended to across runs)
```
The CSV and media directories are created on-demand by their respective scripts.

## Key modules
- **`all_process.py`** – Entry point. Defines `TABLE_DICT` with table metadata, iterates through videos, and calls the downstream modules in order.
- **`video_to_audio_conversion.py`** – Wraps MoviePy to export each video's audio track. Handles missing files or silent videos gracefully.
- **`video_to_image_conversion.py`** – Uses OpenCV to capture frames at a fixed time interval, determined by the `frame_interval_in_seconds` field in `TABLE_DICT`.
- **`image_text_prompting.py`** – Pulls prompts from `tracking_details.csv`, builds a consolidated JSON-format instruction, sends each frame to Groq's multimodal endpoint, and writes binary yes/no flags to `<video>_frame_level.csv`.
- **`audio_to_text.py`** – Loads Groq Whisper + Llama models, transcribes audio, classifies the transcript using the same prompt catalogue (audio-specific prompts), logs raw output, and writes `<video>_audio_result.csv`.
- **`text_to_csv_process.py`** – Combines frame-level and audio-level CSVs, applies post-processing rules (e.g., `_min`, `_max`, `_avg`, `_all` suffixes), computes the source video length, and appends a single summary row to `summary_results.csv`.
- **`mysql_process.py`** – Utility helpers to export prompt definitions from MySQL into `tracking_details.csv`, parse them into prompt dictionaries, and upload final summaries back to MySQL.
- **Utility scripts** – `examine_videos.py` checks whether videos have audio, `frame_rate_calculator.py` prints FPS for a folder, and `delete_file_process.py` clears generated artifacts for a given video ID.

## Configuration
- **Environment variables** – Provide `GROQ_API_KEY` in a `.env` file so that the Groq client can authenticate.
- **Prompt catalogue** – Populate `tracking_details.csv` either manually or by running `mysql_process.export_mysql_table_to_csv`. Each row includes `key`, `type`, `prompt`, optional `time`, and `process` metadata. The `type` column determines whether a prompt applies to video frames, OCR output, or audio.
- **Frame interval** – Adjust `TABLE_DICT["frame_interval_in_seconds"]` to control how frequently frames are sampled.

## Running the pipeline
1. Export or author `tracking_details.csv` with the prompts you want the models to evaluate.
2. Place your `.mp4` files inside `input_videos/`.
3. Update `TABLE_DICT` in `all_process.py` if you need a different frame interval or table name.
4. Run `python all_process.py` to process every video in the folder. Intermediate CSVs and audio files will appear in their respective directories, and a consolidated row per video will be appended to `summary_results.csv`.

## Suggested next steps
- **Automate prompt/table refresh** – Hook `mysql_process.export_mysql_table_to_csv` and `upload_summary_results_to_table` into a scheduler so prompts and results stay in sync with MySQL.
- **Add monitoring & retries** – Wrap Groq API calls with richer error handling/backoff and log metrics (latency, failures, token usage).
- **Extend analytics** – Implement extra aggregation logic in `text_to_csv_process.py` (e.g., confidence scores, per-time-slice summaries) or add visualization notebooks.
- **Optimize media handling** – Consider streaming frame extraction for long videos, caching model responses, or parallelizing per-video processing to improve throughput.

These areas will give newcomers a deeper understanding of the system and highlight where contributions can have immediate impact.
