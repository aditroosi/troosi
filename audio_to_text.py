import os
import base64
import time
import csv
from dotenv import load_dotenv
from groq import Groq
from mysql_process import generate_audio_prompts_from_mysql
import json
# Load GROQ_API_KEY from .env
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

def build_combined_prompt(prompts):
    lines = [
        "For the given image, respond only in JSON format as shown below with 'yes' or 'no' values:",
        '{ "call_action": "yes", "product_showcase": "no", ... }',
        "Use lowercase keys and responses. Analyze the image and give yes or no for the following:"
    ]
    for p in prompts:
        lines.append(f"- {p['key']}: {p['prompt']}")
    return "\n".join(lines)

# Whisper transcription
def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    print(f"🔁 Transcribing {audio_path} using whisper-large-v3 ...")

    response = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=(os.path.basename(audio_path), audio_bytes),
        response_format="text"
    )

    return response.strip()

# Send transcription to LLM with prompts
def run_llm_on_transcript(transcription, prompts):
    #prompt_text = "Based on the following transcription, answer YES or NO for each of the following:\n\n"
    prompt_text = prompts + "\n\n"
    prompt_text += transcription + "\n\n"

    # for p in prompts:
    #     prompt_text += f"- [{p['key']}] {p['prompt']}\n"

    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt_text}]
        }
    ]

    start = time.time()
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        max_tokens=1024
    )
    duration = round(time.time() - start, 2)
    return response.choices[0].message.content.strip(), duration

# Parse LLM output into dictionary {key: 1 or 0}
def parse_response_to_dict(response_text):
    result = {}
    for line in response_text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            result[key.strip()] = 1 if val.strip().lower() == "yes" else 0
    return result
import json
import re

def parse_yes_no_json_to_dict(json_text):
    # Extract JSON block between triple backticks if it exists
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", json_text, re.DOTALL)
    if match:
        json_text = match.group(1)
    else:
        # fallback: try to locate first JSON-looking block
        json_start = json_text.find("{")
        json_end = json_text.rfind("}")
        if json_start != -1 and json_end != -1:
            json_text = json_text[json_start:json_end+1]
        else:
            print("❌ No JSON block found.")
            return {}

    try:
        parsed = json.loads(json_text)
        return {k: 1 if str(v).strip().lower() == "yes" else 0 for k, v in parsed.items()}
    except json.JSONDecodeError as e:
        print("❌ JSON decode failed:", e)
        print("🔍 Raw input was:\n", json_text)
        return {}


# Main function
def transcribe_audio_and_update_file(audio_filename):
    input_audio_path = os.path.join("audio_files", audio_filename)
    base_name = os.path.splitext(audio_filename)[0]
    os.makedirs("individual_frame_responses", exist_ok=True)
    os.makedirs("csv_results", exist_ok=True)
    txt_output_path = os.path.join("individual_frame_responses", f"{base_name}.txt")
    csv_output_path = os.path.join("csv_results", f"{base_name}_audio_result.csv")

    # Step 1: Load prompts
    prompts = generate_audio_prompts_from_mysql()
    combined_prompt = build_combined_prompt(prompts)
    if not prompts:
        print("❌ No prompts retrieved.")
        return
    keys = [p['key'] for p in prompts]

    # Step 2: Handle missing audio
    if not os.path.exists(input_audio_path):
        print(f"⚠️ Audio not found: {input_audio_path}. Saving all 0s.")
        with open(csv_output_path, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["audio_file"] + keys)
            writer.writerow([base_name] + [0] * len(keys))
        return

    # Step 3: Transcribe
    transcription = transcribe_audio(input_audio_path)

    # Step 4: LLM analysis
    llm_response, time_taken = run_llm_on_transcript(transcription, combined_prompt)
    parsed = parse_yes_no_json_to_dict(llm_response)
    # print(parsed)
    # print("\n\n\n\n\n\n\n\nllmm reusinfoiusbu")
    # print(llm_response)
    # Step 5: Save TXT
    with open(txt_output_path, "a", encoding="utf-8") as f:
        f.write(f"\n--- Transcription from audio ---\n{transcription}\n")
        f.write(f"\n--- Prompt-based analysis (Time taken: {time_taken}s) ---\n{llm_response}\n")

    print(f"✅ Transcription + prompt result saved to: {txt_output_path}")

    # Step 6: Save CSV
    with open(csv_output_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["audio_file"] + keys)
        writer.writerow([base_name] + [parsed.get(key, 0) for key in keys])

    print(f"✅ CSV saved to: {csv_output_path}")

if __name__ == "__main__":
    transcribe_audio_and_update_file("1_Priyadeep Kaur.mp3")  # Replace with your actual audio file
