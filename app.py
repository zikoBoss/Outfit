from flask import Flask, request, send_file, jsonify
import requests
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)

API_KEY = "xAyOuB"
session = requests.Session()
IMAGE_TIMEOUT = 6


# ---------------- INFO PAGE ----------------
@app.route("/")
def home():
    return {
        "status": "running",
        "message": "Ziko Outfit API is working",
        "usage": {
            "endpoint": "/api/ziko-outfit-image",
            "method": "GET",
            "params": {
                "uid": "required",
                "key": "required"
            },
            "example": "/api/ziko-outfit-image?uid=12345678&key=xAyOuB"
        }
    }


# ---------------- FETCH PLAYER ----------------
def fetch_player_info(uid):
    try:
        url = f"https://sheihk-anamul-info-ob53.vercel.app/player-info?uid={uid}"
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except:
        return None


# ---------------- FETCH IMAGE ----------------
def fetch_image(url):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None


# ---------------- MAIN API ----------------
@app.route("/api/ziko-outfit-image")
def generate():
    uid = request.args.get("uid")
    key = request.args.get("key")

    # 🔴 missing key
    if not key:
        return jsonify({
            "error": "missing key",
            "hint": "add ?key=xAyOuB"
        }), 400

    # 🔴 invalid key
    if key != API_KEY:
        return jsonify({
            "error": "invalid key",
            "hint": "correct key required"
        }), 401

    # 🔴 missing uid
    if not uid:
        return jsonify({
            "error": "missing uid",
            "hint": "add ?uid=12345678"
        }), 400

    data = fetch_player_info(uid)
    if not data:
        return jsonify({
            "error": "api failed",
            "hint": "check uid or external API"
        }), 500

    items = []

    outfit_ids = data.get("profileInfo", {}).get("clothes", [])[:6]
    for oid in outfit_ids:
        img = fetch_image(f"https://iconapi.wasmer.app/{oid}")
        items.append(img.resize((150, 150)) if img else None)

    pet_id = data.get("petInfo", {}).get("id")
    items.append(fetch_image(f"https://iconapi.wasmer.app/{pet_id}").resize((150, 150)) if pet_id else None)

    weapon_list = data.get("basicInfo", {}).get("weaponSkinShows", [])
    if weapon_list:
        items.append(fetch_image(f"https://iconapi.wasmer.app/{weapon_list[0]}").resize((150, 150)))
    else:
        items.append(None)

    while len(items) < 8:
        items.append(None)

    bg = Image.open("outfit.png").convert("RGBA")
    canvas = bg.copy()

    positions = [
        (350, 30),
        (575, 130),
        (665, 350),
        (575, 550),
        (350, 654),
        (135, 570),
        (47, 340),
        (135, 130)
    ]

    for i, img in enumerate(items):
        if img:
            canvas.paste(img, positions[i], img)

    out = BytesIO()
    canvas.save(out, "PNG")
    out.seek(0)

    return send_file(out, mimetype="image/png")