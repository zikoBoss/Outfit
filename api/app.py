from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)

# --- Configuration ---
API_KEY = "xAyOuB"
BACKGROUND_FILENAME = "outfit.png"
IMAGE_TIMEOUT = 8

# --- Helper: fetch player info ---
def fetch_player_info(uid: str):
    try:
        url = f"https://sheihk-anamul-info-ob53.vercel.app/player-info?uid={uid}"
        r = requests.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# --- Helper: fetch image from URL ---
def fetch_image(url, size=None):
    try:
        r = requests.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        if size:
            img = img.resize(size, Image.LANCZOS)
        return img
    except Exception:
        return None

@app.route('/', methods=['GET'])
def generate():
    uid = request.args.get('uid')
    key = request.args.get('key')

    if key != API_KEY:
        return jsonify({"error": "invalid key"}), 401

    if not uid:
        return jsonify({"error": "missing uid"}), 400

    # 1. 获取玩家数据
    data = fetch_player_info(uid)
    if not data:
        return jsonify({"error": "failed to fetch player info"}), 500

    # 2. 提取服装 ID
    outfit_ids = data.get("profileInfo", {}).get("clothes", [])
    if not outfit_ids:
        outfit_ids = data.get("AccountProfileInfo", {}).get("EquippedOutfit", []) or []

    # 3. 下载图片（最多 6 件衣服 + 宠物 + 武器）
    items = []
    for oid in outfit_ids[:6]:
        img = fetch_image(f"https://iconapi.wasmer.app/{oid}", (150, 150))
        items.append(img)

    # 4. 宠物
    pet_id = data.get("petInfo", {}).get("id")
    pet_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}", (150, 150)) if pet_id else None
    items.append(pet_img)

    # 5. 武器
    weapon_list = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_img = None
    if weapon_list:
        weapon_img = fetch_image(f"https://iconapi.wasmer.app/{weapon_list[0]}", (150, 150))
    items.append(weapon_img)

    # 6. 补齐到 8 个位置
    while len(items) < 8:
        items.append(None)

    # 7. 打开背景图（文件必须和代码在同一个部署包内）
    bg_path = os.path.join(os.path.dirname(__file__), "..", BACKGROUND_FILENAME)
    try:
        bg = Image.open(bg_path).convert("RGBA")
    except Exception as e:
        return jsonify({"error": f"background image missing: {str(e)}"}), 500

    canvas = bg.copy()

    # 8. 固定位置（8 个槽位）
    positions = [
        (350, 30),    # 服装 1
        (575, 130),   # 服装 2
        (665, 350),   # 武器
        (575, 550),   # 服装 3
        (350, 654),   # 宠物
        (135, 570),   # 服装 4
        (47, 340),    # 服装 5
        (135, 130)    # 服装 6
    ]

    for i, img in enumerate(items):
        if img is None:
            continue
        x, y = positions[i]
        canvas.paste(img, (x, y), img)

    # 9. 输出 PNG
    out = BytesIO()
    canvas.save(out, format="PNG")
    out.seek(0)

    return send_file(out, mimetype="image/png")

# Vercel 要求导出一个 app 对象