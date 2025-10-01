import os
from moviepy.editor import VideoFileClip

def diagnose_video_issues(input_folder="input_videos"):
    error_log = []

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv')):
            continue

        video_path = os.path.join(input_folder, filename)
        try:
            clip = VideoFileClip(video_path)

            if clip.audio is None:
                error_log.append((filename, "No audio track found"))
            else:
                print(f"✅ {filename}: OK")

        except OSError as e:
            error_log.append((filename, f"File loading error: {e}"))

        except Exception as e:
            error_log.append((filename, f"Unhandled error: {type(e).__name__}: {e}"))

    # Print summary
    print("\n🧾 Video Diagnostic Summary:")
    if not error_log:
        print("All videos are valid and contain audio.")
    else:
        for fname, reason in error_log:
            print(f"❌ {fname}: {reason}")

if __name__ == "__main__":
    diagnose_video_issues()
