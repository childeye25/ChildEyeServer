import sys, json
sys.path.append("/content/drive/MyDrive/ChildEye_Models/DigitalTwin")

from digital_twin_core import update_twin_from_models

print("🧠 Running Child-Eye Digital Twin Simulation...\n")

# ============================================================
# 🧩 جميع الحالات لاختبار Digital Twin
# ============================================================

cases = [
    {
        "name": "😄 طفل سعيد طبيعي",
        "data": {
            "face_emotion": "happy",
            "cry_emotion": "laugh",
            "hr": 118,
            "rr": 32,
            "temp": 36.9,
            "sleep_state": "awake"
        }
    },
    {
        "name": "😴 طفل متعب أو نعسان",
        "data": {
            "face_emotion": "sleep",
            "cry_emotion": "tired",
            "hr": 95,
            "rr": 24,
            "temp": 36.6,
            "sleep_state": "deep_sleep"
        }
    },
    {
        "name": "🤒 طفل مريض أو عنده حرارة",
        "data": {
            "face_emotion": "cry",
            "cry_emotion": "pain",
            "hr": 140,
            "rr": 42,
            "temp": 38.7,
            "sleep_state": "awake"
        }
    }
]

# ============================================================
# 🚀 تشغيل كل حالة وطباعتها بشكل منسق
# ============================================================

results = []

for c in cases:
    print(f"\n🌼 Running Case: {c['name']}")
    result = update_twin_from_models({}, c["data"])
    print(json.dumps(result, indent=4))
    print("-" * 60)
    results.append({
        "name": c["name"],
        "status": result.get("status"),
        "prediction": result.get("next_prediction"),
        "confidence": result.get("confidence"),
        "reason": result.get("reason")
    })

# ============================================================
# 📊 ملخص النتائج النهائية لكل الحالات
# ============================================================

print("\n✅ TEST RESULTS SUMMARY\n")
print("{:<20} | {:<10} | {:<18} | {:<10} | {}".format(
    "Case", "Status", "Prediction", "Conf.", "Reason"))
print("-" * 90)
for r in results:
    print("{:<20} | {:<10} | {:<18} | {:<10} | {}".format(
        r["name"], r["status"], str(r["prediction"]),
        str(r["confidence"]), r["reason"]
    ))

print("\n🌟 Simulation complete — all Digital Twin tests executed successfully.")
