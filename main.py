from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import time
import threading

app = Flask(__name__)

# Allow CORS for specific frontend domain
CORS(app, resources={r"/*": {"origins": "https://pyeulshares-exclusive-for-owner.onrender.com"}})

def share_post(token, share_url, share_count, results):
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
    for _ in range(share_count * 2):  # Double sharing
        try:
            response = requests.post(url, json=data, headers=headers)
            response_data = response.json()
            if "id" in response_data:
                success_count += 1
        except requests.exceptions.RequestException as e:
            print(f"Failed to share post for token {token[:10]}: {e}")
        time.sleep(0.5)

    results[token] = success_count

@app.route("/share", methods=["POST"])
def share():
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    tokens = data.get("tokens", [])
    share_url = data.get("postLink")
    share_count = data.get("shares", 1)

    if not tokens or not share_url:
        return jsonify({"error": "Missing required fields"}), 400

    threads = []
    results = {}

    for token in tokens:
        thread = threading.Thread(target=share_post, args=(token, share_url, share_count, results))
        thread.start()
        threads.append(thread)
        time.sleep(0.25)

    for thread in threads:
        thread.join()

    response = make_response(jsonify({"success": True, "results": results}))
    response.headers.add("Access-Control-Allow-Origin", "https://pyeulshares-exclusive-for-owner.onrender.com")
    response.headers.add("Access-Control-Allow-Methods", "POST")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
