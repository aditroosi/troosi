import os
import shutil

def delete_path(target_path):
    if not os.path.exists(target_path):
        print(f"❌ Path not found: {target_path}")
        return

    try:
        if os.path.isfile(target_path):
            os.remove(target_path)
            print(f"🗑️ Deleted file: {target_path}")
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
            print(f"🗑️ Deleted folder and all contents: {target_path}")
        else:
            print(f"⚠️ Not a valid file or folder: {target_path}")
    except Exception as e:
        print(f"❌ Error deleting {target_path}: {e}")


def delete_all_files(file_name):
    audio_file_path = os.path.join("audio_files", file_name+".mp3")    
    delete_path(audio_file_path)
    frame_level_csv_path = os.path.join("csv_results", file_name+"_frame_level.csv")    
    delete_path(frame_level_csv_path)
    audio_result_csv_path = os.path.join("csv_results", file_name+"_audio_result.csv")    
    delete_path(audio_result_csv_path)
    extracted_frames_path = os.path.join("extracted_frames", file_name)    
    delete_path(extracted_frames_path)
    individual_frame_responses_path = os.path.join("individual_frame_responses", file_name+".txt")    
    delete_path(individual_frame_responses_path)
    input_videos_path = os.path.join("input_videos", file_name+".mp4")    
    delete_path(input_videos_path)

if __name__ == "__main__":
    # Example usage
    file_name = "1kk"  # Replace with the actual file name you want to delete
    delete_all_files("6")
    print("✅ All related files deleted successfully.")