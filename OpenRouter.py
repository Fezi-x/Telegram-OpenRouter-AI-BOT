from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.post("/chat")
def chat():
    data = request.get_json()
    user_msg = data.get("message", "")
    
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "OPENROUTER_API_KEY not set"}), 500
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "My Chatbot App",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-4-maverick:free",  # Most reliable free model
        "messages": [
            {"role": "user", "content": user_msg}
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        
        # Check HTTP status
        if response.status_code != 200:
            print(f"OpenRouter Error: {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({"error": f"API returned {response.status_code}"}), 500
        
        result = response.json()
        
        # Check for API errors
        if "error" in result:
            print(f"OpenRouter API Error: {result['error']}")
            return jsonify({"error": result["error"]}), 500
        
        # Extract reply safely
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            
            if "message" in choice and "content" in choice["message"]:
                reply = choice["message"]["content"]
            elif "text" in choice:
                reply = choice["text"]
            else:
                return jsonify({"error": "Unexpected response format"}), 500
            
            return jsonify({"reply": reply})
        else:
            return jsonify({"error": "No choices in response"}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)