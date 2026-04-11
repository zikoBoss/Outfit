from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import os

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=10)
session = requests.Session()

# --- Configuration ---
API_KEY = "xAyOuB"
BACKGROUND_FILENAME = "outfit.png"
IMAGE_TIMEOUT = 8

# --- API ---
def fetch_player_info(uid: str):
    try:
        url = f"https://sheihk-anamul-info-ob53.vercel.app/player-info?uid={uid}"
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except:
        return None

# --- Image fetch ---
def fetch_image(url, size=None):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        if size:
            img = img.resize(size, Image.LANCZOS)
        return img
    except:
        return None

@app.route('/ziko-outfit-image', methods=['GET'])
def generate():
    uid = request.args.get('uid')
    key = request.args.get('key')

    if key != API_KEY:
        return jsonify({"error": "invalid key"}), 401

    if not uid:
        return jsonify({"error": "missing uid"}), 400

    data = fetch_player_info(uid)
    if not data:
        return jsonify({"error": "api failed"}), 500

    # --- 👕 الملابس ---
    outfit_ids = data.get("profileInfo", {}).get("clothes", [])
    if not outfit_ids:
        outfit_ids = data.get("AccountProfileInfo", {}).get("EquippedOutfit", []) or []

    valid_items = []

    # 6 ملابس فقط
    for oid in outfit_ids[:6]:
        img = fetch_image(f"https://iconapi.wasmer.app/{oid}", (150, 150))
        valid_items.append(img if img else None)

    # --- 🐾 PET ---
    pet_id = data.get("petInfo", {}).get("id")
    pet_img = None
    if pet_id:
        pet_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}", (150, 150))

    valid_items.append(pet_img)

    # --- 🔫 WEAPON ---
    weapon_list = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_img = None

    if weapon_list:
        weapon_img = fetch_image(f"https://iconapi.wasmer.app/{weapon_list[0]}", (150, 150))

    valid_items.append(weapon_img)

    # تأكد العدد = 8
    while len(valid_items) < 8:
        valid_items.append(None)

    # --- الخلفية ---
    path = os.path.join(os.path.dirname(__file__), BACKGROUND_FILENAME)
    try:
        bg = Image.open(path).convert("RGBA")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    canvas = bg.copy()

    # --- 📍 positions (8 خانات) ---
    positions = [
        (350, 30),    # ملابس
        (575, 130),   # ملابس
        (665, 350),   # 🔫 weapon
        (575, 550),   # ملابس
        (350, 654),   # 🐾 pet
        (135, 570),   # ملابس
        (47, 340),   # ملابس
        (135, 130)    # ملابس
    ]

    # --- paste ---
    for i, img in enumerate(valid_items):
        if not img:
            continue

        x, y = positions[i]
        canvas.paste(img, (x, y), img)

    # --- output ---
    out = BytesIO()
    canvas.save(out, format="PNG")
    out.seek(0)

    return send_file(out, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)