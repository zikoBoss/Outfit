from flask import Flask, request, send_file, jsonify
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

API_KEY = "xAyOuB"
session = requests.Session()
IMAGE_TIMEOUT = 8


def fetch_player_info(uid):
    try:
        url = f"https://sheihk-anamul-info-ob53.vercel.app/player-info?uid={uid}"
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except:
        return None


def fetch_image(url):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None


@app.route("/api/ziko-outfit-image")
def generate():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "invalid key"}), 401

    if not uid:
        return jsonify({"error": "missing uid"}), 400

    data = fetch_player_info(uid)
    if not data:
        return jsonify({"error": "api failed"}), 500

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
