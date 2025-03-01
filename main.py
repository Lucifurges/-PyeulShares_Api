from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import threading

app = Flask(__name__)
CORS(app)

def share_post(token, share_url, share_count):
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
    for i in range(1, share_count * 2 + 1):
        try:
            response = requests.post(url, json=data, headers=headers)
            response_data = response.json()
            post_id = response_data.get("id", None)
            if post_id:
                success_count += 1
        except requests.exceptions.RequestException as e:
            print(f"Failed to share post for token {token[:10]}: {e}")
        time.sleep(0.5)
    return success_count

@app.route("/share", methods=["POST"])
def share():
    data = request.json
    tokens = data.get("tokens", [])
    share_url = data.get("postLink")
    share_count = data.get("shares", 1)

    if not tokens or not share_url:
        return jsonify({"error": "Missing required fields"}), 400

    threads = []
    results = {}
    
    def share_worker(token):
        results[token] = share_post(token, share_url, share_count)
    
    for token in tokens:
        thread = threading.Thread(target=share_worker, args=(token,))
        thread.start()
        threads.append(thread)
        time.sleep(0.25)
    
    for thread in threads:
        thread.join()
    
    return jsonify({"success": True, "results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
