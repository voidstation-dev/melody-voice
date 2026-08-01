from capcut_tts_api import CapCutClient

client = CapCutClient()
text = "Xin chào các bạn, đây là một đoạn text dài để kiểm tra tốc độ đọc của hệ thống."

print("Generating 1.0x...")
r1 = client.generate_speech(text, rate="1.0")
tasks = r1.get("data", {}).get("tasks", [])
if tasks:
    print("Task 1:", tasks[0].get("id"))

print("Generating 2.0x...")
r2 = client.generate_speech(text, rate="2.0")
tasks2 = r2.get("data", {}).get("tasks", [])
if tasks2:
    print("Task 2:", tasks2[0].get("id"))
