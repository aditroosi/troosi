from moviepy.editor import VideoFileClip

def get_video_length(video_path: str) -> float:
    clip = VideoFileClip(video_path)
    duration = clip.duration  # duration in seconds
    clip.close()
    return duration

# # Example usage:
# video_path = "Priyadeep Kaur.mp4"
# length_sec = get_video_length(video_path)
# print(f"Video length: {length_sec:.2f} seconds")