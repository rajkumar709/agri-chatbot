import sqlite3
from datetime import datetime
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

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

def recommend_crop(user_input):

    user_input = user_input.lower()

    if "black soil" in user_input:
        return "Black soil is good for growing cotton and soybean."

    if "clay soil" in user_input:
        return "Clay soil is suitable for rice cultivation."

    if "sandy soil" in user_input:
        return "Sandy soil is good for growing groundnut and watermelon."

    if "high rainfall" in user_input:
        return "High rainfall areas are suitable for rice and sugarcane."

    if "low rainfall" in user_input:
        return "Low rainfall areas are suitable for millets like ragi and jowar."

    return None
import requests

import requests

def get_weather(city):

    API_KEY = "c81827b3ec89ba91d141f002b16f4c85"

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = request.get(url, params=params)
    data = response.json()

    if response.status_code != 200:
        return "Sorry, I couldn't find the weather for that location."

    temperature = data["main"]["temp"]
    description = data["weather"][0]["description"]

    return f"Weather in {city.title()}: {temperature}°C with {description}."

def get_bot_response(user_input):

    user_input = user_input.lower()
    crop_result = recommend_crop(user_input)
    if crop_result:
        return crop_result
    if "ನಮಸ್ಕಾರ" in user_input:
        return "ನಮಸ್ಕಾರ ರೈತರೆ! ನಾನು ನಿಮ್ಮ ಕೃಷಿ ಸಹಾಯಕ ಚಾಟ್‌ಬಾಟ್."
    if "नमस्ते" in user_input:
        return "नमस्ते किसान! मैं आपका कृषि सहायक चैटबॉट हूँ|"
    if "weather in" in user_input:
        city=user_input.replace("weather in","").strip()
        return get_weather(city)

    responses = {

        "rice": "Rice grows well in warm climate with clay soil and regular irrigation.",
        "wheat": "Wheat requires cool climate and well-drained loamy soil.",
        "maize": "Maize grows best in warm weather with fertile, well-drained soil.",
        "cotton": "Cotton requires black soil and warm climate for good yield.",
        "fertilizer": "Use NPK fertilizer (Nitrogen, Phosphorus, Potassium) for better yield.",
        "organic fertilizer": "Organic fertilizers like compost and manure improve soil health.",
        "pest": "Neem oil spray is effective for controlling common crop pests.",
        "irrigation": "Drip irrigation saves water and improves crop productivity.",
        "soil": "Healthy soil contains nutrients, organic matter, air, and water.",
        "weather": "Check local weather forecast before irrigation or spraying pesticides.",
        "scheme": "PM-KISAN scheme provides financial assistance to farmers.",
        "crop rotation": "Crop rotation helps maintain soil fertility and reduce pests.",
        "disease": "Use certified seeds and proper pesticides to prevent crop diseases.",
        "harvest": "Harvest crops at the right maturity stage for better yield and quality.",
        "seed": "Use high-quality certified seeds for better crop productivity."
    }

    for key in responses:
        if key in user_input:
            return responses[key]

    return "Sorry, I can help with crops, fertilizer, pests, irrigation, soil, weather, and government schemes."

@app.route("/", methods=["GET", "POST"])
def home():
    bot_response = ""

    if request.method == "POST":
        user_input = request.form["message"]
        bot_response = get_bot_response(user_input)
        return bot_response

        conn = sqlite3.connect("chatbot.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO chats (question, answer, language, timestamp) VALUES (?, ?, ?, ?)",
            (user_input, bot_response, "English", datetime.now())
        )

        conn.commit()
        conn.close()

    return render_template("index.html", response=bot_response)

if __name__ == "__main__":
    app.run()