import mysql.connector
import csv
import time
import pandas as pd
import  os
def generate_prompts_from_mysql(csv_path="tracking_details.csv"):
    prompt_results = []

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["key"]
                input_type = row["type"].strip().lower()
                prompt_text = row["prompt"].strip()
                csv_time = row["time"].strip()
                process = row["process"].strip().lower()
                

                if "video" in input_type:
                    prompt = f"Based on the video, answer yes or no: {prompt_text}"
                    prompt_results.append({"key": key+"_video__"+str(process), "prompt": prompt, "expected_response": False,"time": csv_time})
                elif "ocr" in input_type:
                    prompt = f"Based on the OCR extracted text, answer yes or no: {prompt_text}"
                    prompt_results.append({"key": key+"_ocr__"+str(process), "prompt": prompt, "expected_response": False,"time": csv_time})

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

    return prompt_results


def generate_audio_prompts_from_mysql(csv_path="tracking_details.csv"):
    prompt_results = []

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["key"]
                input_type = row["type"].strip().lower()
                prompt_text = row["prompt"].strip()

                if "audio" in input_type:
                    prompt = f"Based on the audio, answer yes or no: {prompt_text}"
                    prompt_results.append({"key": key+"_audio", "prompt": prompt, "expected_response": False})

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

    return prompt_results


def generate_prompts_with_time(csv_path="tracking_details.csv"):
    result = []

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                result.append({
                    "key": row["key"],
                    "type": row["type"],
                    "prompt": row["prompt"],
                    "time": int(row["time"]) if row["time"].isdigit() else 0
                })

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")

    return result

def export_mysql_table_to_csv(table_name):
    max_retry_time = 600  # total retry duration limit in seconds
    retry_interval = 5    # initial retry wait
    elapsed_time = 0

    while elapsed_time <= max_retry_time:
        try:
            # Try connecting
            conn = mysql.connector.connect(
                host="13.233.101.29",
                port=3306,
                user="myuser",
                password="mypassword",
                database="mydatabase"
            )
            cursor = conn.cursor()

            # Query all rows
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Write to CSV
            csv_path = f"tracking_details.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(column_names)
                writer.writerows(rows)

            print(f"✅ Table '{table_name}' exported to: {csv_path}")
            break  # success, exit retry loop

        except mysql.connector.Error as e:
            print(f"❌ Connection error: {e}")
            elapsed_time += retry_interval
            if elapsed_time > max_retry_time:
                print("❌ Maximum retry time exceeded. Giving up.")
                break
            print(f"🔁 Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
            retry_interval += 5  # increment wait time for next retry

        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals() and conn.is_connected(): conn.close()

def upload_summary_results_to_table(table_name):
    DB_CONFIG = {
        "host": "13.233.101.29",
        "port": 3306,
        "user": "myuser",
        "password": "mypassword",
        "database": "mydatabase"
    }

    csv_path = "summary_results.csv"
    if not os.path.exists(csv_path):
        print("❌ File not found: summary_results.csv")
        return

    # Read CSV contents
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    # Retry MySQL connection
    conn, cursor = None, None
    retry_delay = 5
    max_wait = 600
    waited = 0
    while waited <= max_wait:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            break
        except Exception as e:
            print(f"❌ MySQL connection failed, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            waited += retry_delay

    if not conn:
        print("❌ Could not connect to MySQL after retries.")
        return

    try:
        # Create table if not exists
        col_defs = ", ".join([f"`{col}` TEXT" for col in headers])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS `{table_name}` ({col_defs})")

        # Insert data
        placeholders = ", ".join(["%s"] * len(headers))
        insert_query = f"INSERT INTO `{table_name}` ({', '.join(headers)}) VALUES ({placeholders})"
        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"✅ Data from summary_results.csv uploaded to table '{table_name}'")

        # Delete the CSV file
        os.remove(csv_path)
        os.remove("tracking_details.csv")
        print(f"🗑️ Deleted: {csv_path}")

    except Exception as e:
        print(f"❌ Error uploading data: {e}")

    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# Example usage
if __name__ == "__main__":
    #export_mysql_table_to_csv("tracking_details")
    #upload_summary_results_to_table("1_skjdg")
    print(generate_prompts_from_mysql( "tracking_details.csv"))