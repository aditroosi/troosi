import cv2
import os

def extract_frames_every_n_seconds(video_filename, seconds):
    input_folder = "input_videos"
    output_folder = f"extracted_frames/{video_filename.replace('.mp4', '')}"
    os.makedirs(output_folder, exist_ok=True)

    video_path = os.path.join(input_folder, video_filename)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Could not open video: {video_filename}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * seconds)
    print(f"🎞️ {video_filename} | FPS: {fps:.2f} | Extract every {seconds}s (every {interval} frames)")

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % interval == 0:
            frame_path = os.path.join(output_folder, f"frame_{frame_idx}.jpg")
            cv2.imwrite(frame_path, frame)

        frame_idx += 1

    cap.release()
    print(f"✅ Done extracting frames from {video_filename}")

if __name__ == "__main__":
    # Example usage
    extract_frames_every_n_seconds("1.mp4", nth=25)
