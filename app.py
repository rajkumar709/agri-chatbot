import sqlite3
from datetime import datetime
from flask import Flask, render_template, request
import requests
from PIL import Image
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)   


# -------------------- AI FUNCTION --------------------
def get_ai_response(user_input):
    import os
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "stepfun/step-3.5-flash:free",  # ✅ FREE MODEL
        "messages": [
            {
                "role": "user",
                "content": f"you are an agriculture expert chatbot. answer in 1-2 sentences. {user_input}"
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print("API RESULT:", result)

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"API Error: {result}"

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

def detect_disease_from_image(filename):
    return get_ai_response(f"Analyze this image and identify any crop diseases: {filename}")


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
    file = request.files["image"]

    if file:
        filename = file.filename
        result = detect_disease_from_image(filename)
        return {"result": result}
    return {"result": "No file uploaded"}

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)