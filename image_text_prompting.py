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
    example_payload = json.dumps(
        {
            "answers": {"call_action": "yes"},
            "reasons": {"call_action": "Visible button with \"Call Now\" text."},
        }
    )

    lines = [
        "Analyze the image and respond strictly in JSON with two top-level objects: 'answers' and 'reasons'.",
        "Each key listed below must appear inside both objects.",
        "'answers' values must be the lowercase strings 'yes' or 'no'.",
        "'reasons' values must be short text snippets (<40 words) that explain the decision using evidence from the image.",
        "Example response:",
        example_payload,
        "Do not include any additional text outside of the JSON response.",
        "Evaluate the following checks:",
    ]
    for p in prompts:
        lines.append(f"- {p['key']}: {p['prompt']}")
    return "\n".join(lines)



def clean_json_text(raw_text: str) -> str:
    """Strip Markdown fences or language hints before parsing JSON."""

    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
        cleaned = cleaned.lstrip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.lstrip()
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]

    return cleaned.strip()


def extract_numeric_sort_key(filename: str):
    digits = "".join(filter(str.isdigit, filename))
    return (int(digits) if digits else float("inf"), filename)


def answer_value_is_yes(value) -> bool:
    """Return True when the provided answer represents an affirmative response."""

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value == 1

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"yes", "true", "1"}:
            return True
        if normalized in {"no", "false", "0"}:
            return False

    return False


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

    reasons_csv_path = os.path.join("csv_results", f"{folder_name}_frame_level_reasons.csv")

    with open(csv_path, "w", newline='', encoding="utf-8") as csvfile, \
         open(reasons_csv_path, "w", newline='', encoding="utf-8") as reasons_csvfile:
        writer = csv.writer(csvfile)
        reasons_writer = csv.writer(reasons_csvfile)
        header = ["frame"] + keys
        writer.writerow(header)
        reasons_writer.writerow(header)

        for file in sorted(os.listdir(input_dir), key=extract_numeric_sort_key):

            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(input_dir, file)
                print(f"Processing: {file}")

                try:
                    json_text, time_taken = send_image_and_get_json(full_path, combined_prompt)

                    # Try parsing JSON from the model
                    parsed = json.loads(clean_json_text(json_text))

                    answers = {}
                    reasons = {}

                    if isinstance(parsed, dict):
                        answers_candidate = parsed.get("answers") if "answers" in parsed else parsed
                        if isinstance(answers_candidate, dict):
                            answers = answers_candidate
                        if "reasons" in parsed and isinstance(parsed["reasons"], dict):
                            reasons = parsed["reasons"]

                    # Write rows to CSVs
                    row = [file] + [1 if answer_value_is_yes(answers.get(k, "")) else 0 for k in keys]
                    writer.writerow(row)

                    reasons_row = [file] + [str(reasons.get(k, "")) for k in keys]
                    reasons_writer.writerow(reasons_row)

                except Exception as e:
                    print(f"❌ Error processing {file}: {e}")

    print(f"✅ CSV saved to: {csv_path}")
    print(f"✅ Reasons CSV saved to: {reasons_csv_path}")

if __name__ == "__main__":
    process_folder_and_store_csv("1")  # Update folder name if needed
