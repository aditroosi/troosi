import cv2
import os

folder_path = "downloaded_videos"

for filename in os.listdir(folder_path):
    if filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        video_path = os.path.join(folder_path, filename)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"❌ Cannot open: {filename}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"✅ {filename} - FPS: {fps:.2f}")
        cap.release()
