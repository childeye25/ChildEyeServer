# ============================================================
# 🌐 Child-Eye Unified Server — Full Production Version
# ============================================================

import os, io, json, traceback
import numpy as np
import librosa
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from tensorflow import keras
from PIL import Image

# ChildEye Modules
from db_connection import get_connection
from DigitalTwin.digital_twin_core import update_twin_from_models

load_dotenv()

# ============================================================
# 🧠 تحميل جميع الموديلات
# ============================================================

def load_all_models():
    MODELS = {}
    base = r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models"

    paths = {
        "face_detection": {
            "model": f"{base}\\FaceEmotion_Model\\best_face_model.keras",
            "meta":  f"{base}\\FaceEmotion_Model\\best_face_model_meta.json",
            "type": "keras",
        },
        "cry_analysis": {
            "model": f"{base}\\CryAnalysis_Model\\CryAnalysis_Model.keras",
            "meta":  f"{base}\\CryAnalysis_Model\\CryAnalysis_Model_meta.json",
            "type": "keras",
        },
        "fusion_hr_rr": {
            "model": f"{base}\\Fusion_Model_HR_RR\\best_fusion_model.keras",
            "meta":  f"{base}\\Fusion_Model_HR_RR\\best_fusion_model_meta.json",
            "type": "keras",
        },
        "sleep_rules": {
            "model": f"{base}\\SleepRules\\sleep_rules.py",
            "meta":  f"{base}\\SleepRules\\sleep_rules_meta.json",
            "type": "rule",
        },
        "temperature_rules": {
            "model": f"{base}\\TemperatureRules\\temp_rules.py",
            "meta":  f"{base}\\TemperatureRules\\temp_rules_meta.json",
            "type": "rule",
        },
    }

    for name, info in paths.items():
        m_path = info["model"]
        meta = info["meta"]
        m_type = info["type"]

        if not os.path.exists(m_path):
            print(f"❌ {name} missing: {m_path}")
            continue

        metadata = {}
        if os.path.exists(meta):
            try:
                with open(meta, "r") as f:
                    metadata = json.load(f)
            except:
                metadata = {}

        if m_type == "keras":
            try:
                model = keras.models.load_model(m_path)
                MODELS[name] = {"model": model, "meta": metadata}
                print(f"✅ Loaded model: {name}")
            except Exception as e:
                print(f"❌ Failed loading {name}: {e}")

        else:
            MODELS[name] = {"path": m_path, "meta": metadata}
            print(f"📄 Rule model registered: {name}")

    print("\n📦 Loaded Models:")
    for m in MODELS:
        print(f"   - {m}")

    return MODELS


# ============================================================
# 🎧 معالجة الصوت
# ============================================================

def preprocess_audio(file_bytes):
    y, sr = librosa.load(io.BytesIO(file_bytes), sr=16000)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_db = librosa.power_to_db(S, ref=np.max)
    S_norm = (S_db - S_db.min()) / (S_db.max() - S_db.min() + 1e-8)
    img = (S_norm * 255).astype(np.uint8)

    arr = Image.fromarray(np.stack([img, img, img], -1))
    arr = arr.resize((224, 224))
    arr = np.array(arr, dtype=np.float32) / 255.0
    return np.expand_dims(arr, 0)


# ============================================================
# 🗄️ DB Saving Functions (History Tables)
# ============================================================

def save_sleep_history(child_id, hr, rr, state):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sleep_history (child_id, heart_rate, resp_rate, sleep_state)
            VALUES (%s, %s, %s, %s)
        """, (child_id, hr, rr, state))
        conn.commit()
    except Exception as e:
        print("sleep_history error:", e)
    finally:
        cur.close()
        conn.close()

def save_temp_history(child_id, temp, state):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO temp_history (child_id, temperature, temp_state)
            VALUES (%s, %s, %s)
        """, (child_id, temp, state))
        conn.commit()
    except Exception as e:
        print("temp_history error:", e)
    finally:
        cur.close()
        conn.close()

def save_hunger_history(child_id, cry_type, hunger_score):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO hunger_history (child_id, cry_type, hunger_score)
            VALUES (%s, %s, %s)
        """, (child_id, cry_type, hunger_score))
        conn.commit()
    except Exception as e:
        print("hunger_history error:", e)
    finally:
        cur.close()
        conn.close()


# ============================================================
# 🚀 تشغيل Flask
# ============================================================

app = Flask(__name__)
CORS(app)

print("🔧 Loading models...")
MODELS = load_all_models()
print("✅ All Models Loaded!")


# ============================================================
# 📌 API: test & status
# ============================================================

@app.route("/status", methods=["GET"])
def status():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM vitals ORDER BY timestamp DESC LIMIT 1
        """)
        row = cur.fetchone()

        if not row:
            return jsonify({"status": "no_data"})

        # تحديث التوأم الرقمي
        twin_input = {
            "hr": row["heart_rate"],
            "rr": row["resp_rate"],
            "temp": row["temperature"],
            "cry_emotion": row.get("cry_classification", "silence"),
            "face_emotion": row.get("emotion_status", "neutral")
        }
        twin_state = update_twin_from_models(MODELS, twin_input)

        return jsonify({
            "status": "ok",
            "vitals": row,
            "digital_twin": twin_state
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Child-Eye Server is running!", "models": list(MODELS.keys())})


# ============================================================
# 📌 API: Update Vitals from Raspberry Pi
# ============================================================

@app.route("/update_vitals", methods=["POST"])
def update_vitals():
    try:
        data = request.json
        child_id = data.get("child_id", 1)

        hr = data.get("heart_rate")
        rr = data.get("resp_rate")
        temp = data.get("temperature")
        cry = data.get("cry_type", "silence")
        emo = data.get("emotion", "neutral")

        # 1) حفظ القراءة في vitals
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO vitals (child_id, heart_rate, resp_rate, temperature, cry_classification, emotion_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (child_id, hr, rr, temp, cry, emo))
        conn.commit()

        # 2) history tables
        save_sleep_history(child_id, hr, rr, "good")
        save_temp_history(child_id, temp, "normal")
        save_hunger_history(child_id, cry, 0.5)

        # 3) تحديث التوأم الرقمي
        twin_input = {
            "hr": hr,
            "rr": rr,
            "temp": temp,
            "cry_emotion": cry,
            "face_emotion": emo
        }
        twin_state = update_twin_from_models(MODELS, twin_input)

        return jsonify({
            "status": "saved",
            "digital_twin": twin_state
        })

    except Exception as e:
        return jsonify({"error": str(e)})


# ============================================================
# 📌 API: Cry Analysis (Upload Audio)
# ============================================================

@app.route("/predict/cry", methods=["POST"])
def predict_cry():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        cry_model = MODELS["cry_analysis"]["model"]
        meta = MODELS["cry_analysis"]["meta"]
        file = request.files["file"]

        x = preprocess_audio(file.read())
        preds = cry_model.predict(x, verbose=0)[0]
        preds = preds / (np.sum(preds) + 1e-8)

        classes = meta.get("output_classes",
            ["hungry", "pain", "laugh", "noise", "cold_hot", "silence"]
        )

        top = int(np.argmax(preds))
        result = {
            "cry_type": classes[top],
            "confidence": float(preds[top]),
            "all_probs": {classes[i]: float(preds[i]) for i in range(len(preds))}
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


# ============================================================
# ▶️ بدء التشغيل
# ============================================================

if __name__ == "__main__":
    print("🌍 Child-Eye Server running on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
