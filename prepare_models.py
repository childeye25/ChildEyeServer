# ============================================================
# 🧠 Child-Eye Model Preparation Script (Final Corrected)
# ============================================================

import os
import json
import importlib.util
from pathlib import Path
from tensorflow import keras

# ============================================================
# 🔹 المسارات الثابتة لكل وحدة (محدّثة بدقة)
# ============================================================

PATHS = {
    "face_detection": {
        "model": r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\FaceEmotion_Model\best_face_model.keras",
        "meta":  r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\FaceEmotion_Model\best_face_model_meta.json",
        "type": "keras"
    },
    "cry_analysis": {
        "model": r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\CryAnalysis_Model\CryAnalysis_Model.keras",
        "meta":  r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\CryAnalysis_Model\CryAnalysis_Model_meta.json",
        "type": "keras"
    },
    "vision": {
        "model": r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\Fusion_Model_HR_RR\best_fusion_model.keras",
        "meta":  r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\Fusion_Model_HR_RR\best_fusion_model_meta.json",
        "type": "keras"
    },
    "sleep_rules": {
        "model": r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\SleepRules\sleep_rules.py",
        "meta":  r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\SleepRules\sleep_rules_meta.json",
        "type": "rule"
    },
    "temperature_rules": {
        "model": r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\TemperatureRules\temp_rules.py",
        "meta":  r"C:\Users\dhayq\Desktop\GP-Code\ChildEyeServer\ChildEye_Models\TemperatureRules\temp_rules_meta.json",
        "type": "rule"
    }
}

# ============================================================
# 🧩 تحميل الميتاداتا
# ============================================================

def load_metadata(meta_path):
    try:
        with open(meta_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load metadata from {meta_path}: {e}")
        return {}

# ============================================================
# ⚙️ تحميل ملفات .py للقواعد (Sleep / Temperature)
# ============================================================

def load_rule_module(py_path, module_name="rules"):
    try:
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"⚠️ Error loading rule module {py_path}: {e}")
        return None

# ============================================================
# 🚀 تهيئة جميع الموديلات والقواعد
# ============================================================

def prepare_all_models():
    MODELS = {}

    for name, info in PATHS.items():
        model_path = info["model"]
        meta_path  = info["meta"]
        model_type = info["type"]

        if not os.path.exists(model_path):
            print(f"❌ {name}: Model file not found → {model_path}")
            continue

        # ✅ تحميل الميتاداتا
        if not os.path.exists(meta_path):
            if model_type == "rule":
                print(f"ℹ️ {name}: no metadata (rule-only mode)")
                metadata = {}
            else:
                print(f"⚠️ {name}: Metadata not found → {meta_path}")
                metadata = {}
        else:
            metadata = load_metadata(meta_path)

        # ✅ تحميل الموديل أو القاعدة
        if model_type == "keras":
            try:
                model = keras.models.load_model(model_path)
                MODELS[name] = {"model": model, "meta": metadata}
                print(f"✅ Loaded Keras model: {name}")
            except Exception as e:
                print(f"❌ Failed to load {name}: {e}")

        elif model_type == "rule":
            module_name = f"rules_{name}_{Path(model_path).stem}"
            module = load_rule_module(model_path, module_name=module_name)
            if module:
                MODELS[name] = {"module": module, "meta": metadata}
                print(f"✅ Loaded Rule module: {name}")
            else:
                print(f"❌ Failed to load rule: {name}")

    print("\n📦 Summary:")
    for k in MODELS.keys():
        print(f"   - {k} → Ready ✅")

    return MODELS

# ============================================================
# 🔧 إعلان الدالة في النطاق العام
# ============================================================
globals()["prepare_all_models"] = prepare_all_models
__all__ = ["prepare_all_models"]

# ============================================================
# ✅ تشغيل مباشر عند التنفيذ
# ============================================================
if __name__ == "__main__":
    MODELS = prepare_all_models()
    print("\nAll models prepared successfully.")
