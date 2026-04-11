from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)

API_KEY = "xAyOuB"
IMAGE_TIMEOUT = 8

def fetch_player_info(uid):
    try:
        r = requests.get(f"https://sheihk-anamul-info-ob53.vercel.app/player-info?uid={uid}", timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except:
        return None

def fetch_image(url, size=None):
    try:
        r = requests.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        if size:
            img = img.resize(size, Image.LANCZOS)
        return img
    except:
        return None

@app.route('/')
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

    outfit_ids = data.get("profileInfo", {}).get("clothes", [])
    if not outfit_ids:
        outfit_ids = data.get("AccountProfileInfo", {}).get("EquippedOutfit", []) or []

    items = []
    for oid in outfit_ids[:6]:
        items.append(fetch_image(f"https://iconapi.wasmer.app/{oid}", (150, 150)))

    pet_id = data.get("petInfo", {}).get("id")
    pet_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}", (150, 150)) if pet_id else None
    items.append(pet_img)

    weapon_list = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_img = None
    if weapon_list:
        weapon_img = fetch_image(f"https://iconapi.wasmer.app/{weapon_list[0]}", (150, 150))
    items.append(weapon_img)

    while len(items) < 8:
        items.append(None)

    # مسار الصورة الخلفية (صعود لمجلد الجذر)
    bg_path = os.path.join(os.path.dirname(__file__), "..", "outfit.png")
    try:
        bg = Image.open(bg_path).convert("RGBA")
    except:
        return jsonify({"error": "background image not found"}), 500

    canvas = bg.copy()
    positions = [
        (350, 30), (575, 130), (665, 350), (575, 550),
        (350, 654), (135, 570), (47, 340), (135, 130)
    ]

    for i, img in enumerate(items):
        if img:
            canvas.paste(img, positions[i], img)

    out = BytesIO()
    canvas.save(out, format="PNG")
    out.seek(0)
    return send_file(out, mimetype="image/png")