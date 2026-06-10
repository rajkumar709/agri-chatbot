import sqlite3
from datetime import datetime
from flask import Flask, render_template, request
import requests
from PIL import Image


app = Flask(__name__)   


# -------------------- AI FUNCTION --------------------
def get_ai_response(user_input, base64_image=None):
    import os
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    if not OPENROUTER_API_KEY:
        OPENROUTER_API_KEY = "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"

    print("KEY:", OPENROUTER_API_KEY)

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    

    if base64_image:
        content_payload = [
            {"type": "text", "text": f"Analyze this image and identify any crop diseases: {user_input}"},
            {"type": "image_url", "image_url": {
                "url":f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
    else:
        content_payload = f"you are an agriculture expert chatbot. answer in 1-2 sentences. {user_input}"   
    data = {
        "model": "poolside/laguna-m.1:free", # ✅ FREE MODEL       
        "messages": [
            {
                "role": "user",
                "content": """You are Agri AI Assistant.
                Answer ONLY about agriculture-related queries.
                Topics:
                - Crops
                - Diseases
                - Weather
                - Fertilizers
                - Irrigation
                - Pest Control
                - Soil Types
                - Farming Techniques
                - Market Prices
                - Crop Recommendations
                - Sustainable Practices
                - Government Schemes
                - Agricultural News
                
                if the question is not related to agriculture, reply:
                    "Sorry, I can only answer agriculture-related questions."""
            },
            {
                "role": "user",
                "content": content_payload
            }
        ]
    }

    

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print("API RESULT:", result)

        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            if "error" in result:
                return f"API Error: {result['error']}"
        return "the AI analyzed the image but didn't return a valid response."

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------- DATABASE --------------------
def init_db():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            language TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# -------------------- WEATHER --------------------
def get_weather(city):
    API_KEY = "c81827b3ec89ba91d141f002b16f4c85"

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)
    print("Status Code:", response.status_code)
    print("Response:", response.text)

    data = response.json()

    if response.status_code != 200:
        return "Sorry, I couldn't find the weather."

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]

    return f"Weather in {city}: {temp}°C with {desc}"


# -------------------- CROP RECOMMENDATION --------------------
def recommend_crop(user_input):
    user_input = user_input.lower()

    if "black soil" in user_input:
        return "Recommended crops: Cotton, Soybean"

    if "clay soil" in user_input:
        return "Recommended crops: Rice"

    if "sandy soil" in user_input:
        return "Recommended crops: Groundnut, Watermelon"

    return None


# -------------------- BOT LOGIC --------------------
def get_bot_response(user_input):
    user_input = user_input.lower()

    # Crop logic
    crop = recommend_crop(user_input)
    if crop:
        return crop

    # Weather
    if "weather in" in user_input:
        city = user_input.replace("weather in", "").strip()
        return get_weather(city)

    # Local responses
    responses = {
        "rice": "Rice grows well in warm climate with irrigation.",
        "wheat": "Wheat requires cool climate.",
        "fertilizer": "Use NPK fertilizers.",
        "pest": "Neem oil is effective.",
        "irrigation": "Drip irrigation saves water."
    }

    for key in responses:
        if  user_input.strip() in responses:
            return responses[user_input.strip()]

    # 🤖 AI fallback
    return get_ai_response(user_input)

def detect_disease_from_image(file_storage):
    try:
        import base64
        image_bytes = file_storage.read()
        base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
        img = Image.open(file_storage.stream)
        img = img.resize((224, 224))
    
        return get_ai_response("Analyze this image and identify any crop diseases:", base64_image=base64_encoded)
    except Exception as e:
        return f"Error processing image: {str(e)}"
    

# -------------------- ROUTES --------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]
    bot_response = get_bot_response(user_input)

    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO chats (question, answer, language, timestamp) VALUES (?, ?, ?, ?)",
        (user_input, bot_response, "English", datetime.now())
    )

    conn.commit()
    conn.close()

    return {"response": bot_response}

@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return {"result": "No file part"}
    
    file = request.files["image"]

    if file and file.filename != "":
        result = detect_disease_from_image(file)
        return {"result": result}
    
    return {"result": "No file uploaded"}

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)