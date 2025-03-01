from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import time
import threading

app = Flask(__name__)
CORS(app, resources={r"/share": {"origins": ["*"]}})  # Allow all origins for now

def share_post(token, share_url, share_count, delay, results):
    url = "https://graph.facebook.com/me/feed"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {
        "link": share_url,
        "privacy": '{"value":"SELF"}',
        "no_story": "true",
        "published": "false",
        "access_token": token
    }

    success_count = 0
    for _ in range(share_count):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=5)
            response_data = response.json()

            if response.status_code == 200 and "id" in response_data:
                success_count += 1
            else:
                print(f"Failed to share: {response_data}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed for token {token[:10]}: {e}")
        
        time.sleep(delay)

    results[token] = success_count

@app.route("/share", methods=["POST", "OPTIONS"])
def share():
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    tokens = data.get("tokens", [])
    share_url = data.get("postLink")
    share_count = data.get("shares", 1)
    delay = float(data.get("delay", 0.5))

    if not tokens or not share_url:
        return jsonify({"error": "Missing required fields"}), 400

    threads = []
    results = {}

    for token in tokens:
        thread = threading.Thread(target=share_post, args=(token, share_url, share_count, delay, results))
        thread.start()
        threads.append(thread)
        time.sleep(0.1)

    for thread in threads:
        thread.join()

    response = make_response(jsonify({"success": True, "results": results}))
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
