from flask import Flask, request, send_file, jsonify
import requests
from PIL import Image
from io import BytesIO
import os
from functools import lru_cache

app = Flask(__name__)

API_KEY = "xAyOuB"
IMAGE_TIMEOUT = 6

session = requests.Session()
session.headers.update({"Connection": "keep-alive"})


# ---------------- CACHE (مهم فـ Vercel ⚡) ----------------
@lru_cache(maxsize=256)
def cached_player_info(uid):
    try:
        url = f"https://sheihk-anamul-info-ob53.vercel.app/player-info?uid={uid}"
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except:
        return None


@lru_cache(maxsize=512)
def cached_image(url):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None


def fetch_image(url, size=(150, 150)):
    img = cached_image(url)
    if img:
        return img.resize(size)
    return None


# ---------------- MAIN API ----------------
@app.route("/api/ziko-outfit-image")
def generate():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "invalid key"}), 401

    if not uid:
        return jsonify({"error": "missing uid"}), 400

    data = cached_player_info(uid)
    if not data:
        return jsonify({"error": "api failed"}), 500

    items = []

    # ---------------- OUTFITS ----------------
    outfit_ids = data.get("profileInfo", {}).get("clothes") \
                  or data.get("AccountProfileInfo", {}).get("EquippedOutfit", []) \
                  or []

    for oid in outfit_ids[:6]:
        items.append(fetch_image(f"https://iconapi.wasmer.app/{oid}"))

    # ---------------- PET (safe) ----------------
    pet_id = data.get("petInfo", {}).get("id")
    pet_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}") if pet_id else None
    items.append(pet_img)

    # ---------------- WEAPON (safe) ----------------
    weapon_list = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_img = fetch_image(f"https://iconapi.wasmer.app/{weapon_list[0]}") if weapon_list else None
    items.append(weapon_img)

    # ---------------- FILL EMPTY ----------------
    while len(items) < 8:
        items.append(None)

    # ---------------- BACKGROUND ----------------
    bg_path = os.path.join(os.path.dirname(__file__), "outfit.png")

    try:
        bg = Image.open(bg_path).convert("RGBA")
    except:
        return jsonify({"error": "background missing"}), 500

    canvas = bg.copy()

    # ---------------- POSITIONS ----------------
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

    # ---------------- DRAW ----------------
    for i, img in enumerate(items):
        if img:
            canvas.paste(img, positions[i], img)

    # ---------------- OUTPUT ----------------
    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    output.seek(0)

    return send_file(output, mimetype="image/png")