from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import time
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

progress_data = {}  # Stores progress for each request (keyed by request_id)

def share_post(request_id, token, share_url, share_count, delay):
    url = "https://graph.facebook.com/me/feed"
    headers = {"User-Agent": "Mozilla/5.0"}

    for i in range(share_count):
        data = {
            "link": share_url,
            "privacy": '{"value":"SELF"}',
            "no_story": "true",
            "published": "false",
            "access_token": token
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=5)
            response_data = response.json()

            if response.status_code == 200 and "id" in response_data:
                print(f"Shared successfully: {response_data['id']}")
            else:
                print(f"Failed to share: {response_data}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed for token {token[:10]}: {e}")

        # Update progress
        progress_data[request_id]["completed"] += 1
        time.sleep(delay)

    progress_data[request_id]["status"] = "Completed"

@app.route("/share", methods=["POST"])
def share():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    tokens = data.get("tokens", [])
    share_url = data.get("postLink")
    share_count = data.get("shares", 1)
    delay = float(data.get("delay", 0.5))
    request_id = str(time.time())  # Unique ID for tracking

    if not tokens or not share_url:
        return jsonify({"error": "Missing required fields"}), 400

    progress_data[request_id] = {
        "status": "Processing",
        "completed": 0,
        "total": share_count * len(tokens)
    }

    for token in tokens:
        thread = threading.Thread(target=share_post, args=(request_id, token, share_url, share_count, delay))
        thread.daemon = True
        thread.start()

    return jsonify({"request_id": request_id}), 202  # 202 Accepted

@app.route("/progress/<request_id>", methods=["GET"])
def get_progress(request_id):
    return jsonify(progress_data.get(request_id, {"error": "Invalid request ID"}))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
