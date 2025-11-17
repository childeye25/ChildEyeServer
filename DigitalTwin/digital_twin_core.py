# ============================================================
# 🧠 Child-Eye Digital Twin Core — Windows Integrated Version
# ============================================================

import os
import json
from datetime import datetime
from statistics import mean
from collections import Counter

# ============================================================
# 🔹 المسار النهائي على جهازك (Windows)
# ============================================================

BASE_PATH = r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\DigitalTwin"
os.makedirs(BASE_PATH, exist_ok=True)

STATE_FILE = os.path.join(BASE_PATH, "digital_twin_state.json")
HISTORY_FILE = os.path.join(BASE_PATH, "digital_twin_history.json")
REPORT_FILE = os.path.join(BASE_PATH, "digital_twin_report.json")


# ============================================================
# 🔹 التحليل الذكي لحالة الطفل
# ============================================================

def analyze_child_state(face_emotion=None, cry_emotion=None,
                        hr=None, rr=None, temp=None, sleep_state=None):

    status = "normal"
    reason = "stable and healthy"
    confidence = 0.90

    # 🌡️ تحليل الحرارة
    if temp is not None:
        if temp >= 39:
            status, reason = "alert", "High fever (>39°C)"
        elif temp >= 38:
            status, reason = "warning", "Mild fever"
        elif temp < 36:
            status, reason = "warning", "Low body temperature"

    # ❤️‍🔥 تحليل HR/RR
    if hr and rr:
        if hr > 140 or rr > 45:
            status, reason = "alert", "High HR/RR → stress or pain"
        elif hr < 90 or rr < 20:
            status, reason = "warning", "Low HR/RR → deep sleep"

    # 🙂 تحليل الوجه
    if face_emotion:
        if face_emotion == "cry":
            status, reason = "alert", "Face shows crying/distress"
        elif face_emotion == "sleep":
            status, reason = "sleeping", "Eyes closed, calm expression"

    # 🔊 تحليل البكاء
    if cry_emotion:
        if cry_emotion in ["pain", "discomfort"]:
            status, reason = "alert", "Cry indicates pain"
        elif cry_emotion == "hungry":
            status, reason = "warning", "Cry indicates hunger"
        elif cry_emotion == "laugh":
            reason = "Baby laughing → positive mood"

    # دمج المؤشرات
    match_count = 0
    if face_emotion == "cry" and cry_emotion in ["pain"]:
        match_count += 1
    if temp and temp > 38 and "fever" in reason:
        match_count += 1

    confidence = min(0.8 + (match_count * 0.05), 0.99)

    return {
        "status": status,
        "reason": reason,
        "confidence": round(confidence, 2)
    }


# ============================================================
# 🔹 أدوات قراءة/تحليل التاريخ
# ============================================================

def load_history(limit=50):
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data[-limit:] if isinstance(data, list) else []
    except:
        return []

def extract_series(history, key):
    vals = []
    for h in history:
        v = h.get("indicators", {}).get(key)
        if isinstance(v, (int, float)):
            vals.append(v)
    return vals

def trend_last(values, tail=5):
    if len(values) < 2:
        return 0
    n = min(len(values), max(2, tail))
    sub = values[-n:]
    mid = len(sub) // 2
    first, second = sub[:mid], sub[mid:]
    if not first or not second:
        return 0
    return mean(second) - mean(first)

def ratio(arr):
    return sum(1 for x in arr if x) / len(arr) if arr else 0


# ============================================================
# 🔮 التنبؤ بالحالة القادمة (حسب الاتجاهات)
# ============================================================

def predict_next_state_from_history(current_state):
    history = load_history(limit=50)

    if len(history) < 5:
        if current_state["status"] == "alert": return "monitor_closely"
        if current_state["status"] == "sleeping": return "likely_resting"
        return "stable"

    hrs  = extract_series(history, "hr")
    rrs  = extract_series(history, "rr")
    tmps = extract_series(history, "temp")

    tr_hr  = trend_last(hrs,  tail=8)
    tr_rr  = trend_last(rrs,  tail=8)
    tr_tmp = trend_last(tmps, tail=8)

    recent = history[-10:]
    alerts   = ratio([r.get("status") == "alert"   for r in recent])
    warnings = ratio([r.get("status") == "warning" for r in recent])
    sleeping = ratio([r.get("status") == "sleeping" for r in recent])

    if alerts >= 0.3 and (tr_hr > 0.3 or tr_rr > 0.3 or tr_tmp > 0.3):
        return "risk_of_alert"

    if alerts < 0.2 and tr_hr < -0.3 and tr_rr < -0.3:
        return "likely_recovering"

    if sleeping > 0.4 and tr_hr <= 0 and tr_rr <= 0:
        return "likely_resting"

    if (alerts + warnings) >= 0.4:
        return "monitor_closely"

    return "stable"


# ============================================================
# 💾 حفظ حالة التوأم الرقمي + التاريخ
# ============================================================

def update_twin_json(final_state):

    # حفظ حالة التوأم الحالية
    with open(STATE_FILE, "w") as f:
        json.dump(final_state, f, indent=4)

    # تحديث التاريخ
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []
    else:
        history = []

    history.append({
        "timestamp": final_state["timestamp"],
        "status": final_state["status"],
        "reason": final_state["reason"],
        "indicators": final_state["indicators"]
    })

    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-200:], f, indent=4)

    print("📝 Digital Twin JSON updated.")


# ============================================================
# 🔧 الدالة الرئيسية للتوأم الرقمي
# ============================================================

def update_twin_from_models(MODELS, latest_data=None):

    hr   = latest_data.get("hr")
    rr   = latest_data.get("rr")
    temp = latest_data.get("temp")
    face = latest_data.get("face_emotion")
    cry  = latest_data.get("cry_emotion")
    sleep = latest_data.get("sleep_state")

    # تحليل الحالة الحالية
    analysis = analyze_child_state(face, cry, hr, rr, temp, sleep)

    # تنبؤ بالحالة القادمة
    prediction = predict_next_state_from_history(analysis)

    final_state = {
        "timestamp": datetime.now().isoformat(),
        "status": analysis["status"],
        "reason": analysis["reason"],
        "confidence": analysis["confidence"],
        "prediction": prediction,
        "indicators": {
            "hr": hr,
            "rr": rr,
            "temp": temp,
            "face_emotion": face,
            "cry_emotion": cry,
            "sleep_state": sleep
        }
    }

    update_twin_json(final_state)
    return final_state


# ============================================================
# 📊 تقرير كامل للتوأم الرقمي
# ============================================================

def generate_twin_report():
    history = load_history(limit=1000)
    if not history:
        return None

    statuses = [h["status"] for h in history]
    reasons  = [h["reason"] for h in history]

    hrs  = extract_series(history, "hr")
    rrs  = extract_series(history, "rr")
    tmps = extract_series(history, "temp")

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(history),
        "avg_hr": round(mean(hrs), 2) if hrs else None,
        "avg_rr": round(mean(rrs), 2) if rrs else None,
        "avg_temp": round(mean(tmps), 2) if tmps else None,
        "most_common_status": Counter(statuses).most_common(1)[0][0] if statuses else None,
        "dominant_reason": Counter(reasons).most_common(1)[0][0] if reasons else None,
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=4)

    return report


# ============================================================
# 🧹 مسح التوأم بالكامل
# ============================================================

def reset_twin_history():
    for file in [STATE_FILE, HISTORY_FILE, REPORT_FILE]:
        if os.path.exists(file):
            os.remove(file)
    return {"status": "reset_done"}


# ============================================================
# 🔧 اختبار سريع
# ============================================================

if __name__ == "__main__":
    dummy = {
        "hr": 120,
        "rr": 35,
        "temp": 37.5,
        "face_emotion": "neutral",
        "cry_emotion": "silence",
        "sleep_state": "awake"
    }
    print(update_twin_from_models({}, dummy))
