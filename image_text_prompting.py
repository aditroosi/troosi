import os
import time
import base64
import json
import csv
from dotenv import load_dotenv
from groq import Groq
from mysql_process import generate_prompts_from_mysql

# Load env
load_dotenv(dotenv_path=".env", override=True)
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

def build_combined_prompt(prompts):
    lines = [
        "For the given image, respond only in JSON format as shown below with 'yes' or 'no' values:",
        '{ "call_action": "yes", "product_showcase": "no", ... }',
        "Use lowercase keys and responses. Analyze the image and give yes or no for the following:"
    ]
    for p in prompts:
        lines.append(f"- {p['key']}: {p['prompt']}")
    return "\n".join(lines)

def send_image_and_get_json(image_path, prompt):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    }]

    start = time.time()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=2048
    )
    duration = round(time.time() - start, 2)
    return response.choices[0].message.content.strip(), duration

def process_folder_and_store_csv(folder_name):
    input_dir = os.path.join("extracted_frames", folder_name)
    os.makedirs("csv_results", exist_ok=True)
    csv_path = os.path.join("csv_results", f"{folder_name}_frame_level.csv")

    if not os.path.exists(input_dir):
        print(f"❌ Folder not found: {input_dir}")
        return

    prompts = generate_prompts_from_mysql()
    if not prompts:
        print("❌ No prompts found in database.")
        return

    keys = [p["key"] for p in prompts]
    combined_prompt = build_combined_prompt(prompts)

    with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["frame"] + keys)

        for file in sorted(os.listdir(input_dir), key=lambda x: int(''.join(filter(str.isdigit, x)))):

            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(input_dir, file)
                print(f"Processing: {file}")

                try:
                    json_text, time_taken = send_image_and_get_json(full_path, combined_prompt)

                    # Try parsing JSON from the model
                    json_text = json_text.strip("```json").strip("```").strip()
                    parsed = json.loads(json_text)

                    # Write row to CSV
                    row = [file] + [1 if parsed.get(k, "").strip().lower() == "yes" else 0 for k in keys]
                    writer.writerow(row)

                except Exception as e:
                    print(f"❌ Error processing {file}: {e}")

    print(f"✅ CSV saved to: {csv_path}")

if __name__ == "__main__":
    process_folder_and_store_csv("1")  # Update folder name if needed
