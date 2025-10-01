from moviepy.editor import VideoFileClip
import os

def extract_audio_from_input_videos(video_filename):
    input_folder = "input_videos"
    output_folder = "audio_files"
    os.makedirs(output_folder, exist_ok=True)

    video_path = os.path.join(input_folder, video_filename)

    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found - {video_path}")
        return

    audio_filename = os.path.splitext(video_filename)[0] + ".mp3"
    output_audio_path = os.path.join(output_folder, audio_filename)

    clip = VideoFileClip(video_path)

    if clip.audio is None:
        print(f"⚠️ No audio track found in: {video_filename}")
        return

    clip.audio.write_audiofile(output_audio_path)
    print(f"✅ Audio extracted and saved to: {output_audio_path}")

if __name__ == "__main__":
    extract_audio_from_input_videos("1.mp4")
