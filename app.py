from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session, flash
from datetime import datetime
from io import BytesIO
from functools import wraps
import os
import csv
import json
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# pyrefly: ignore [missing-import]
from supabase import create_client, Client


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ewellness_frontend_demo_secret")


# --------------------------------------------------
# SUPABASE CONFIGURATION
# --------------------------------------------------

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

try:
    if supabase_url and supabase_key:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase initialized successfully")
    else:
        print("Supabase initialization error: Missing credentials")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set in .env file")
        supabase = None
except Exception as e:
    print(f"Supabase initialization error: {e}")
    print("Please ensure SUPABASE_URL and SUPABASE_KEY are set correctly in .env file")
    supabase = None


# --------------------------------------------------
# SUPABASE HELPER FUNCTIONS
# --------------------------------------------------

def get_patients():
    if supabase is None:
        return []
    try:
        response = supabase.table('patients').select('*').order('id', desc=False).execute()
        patients = response.data or []
        if patients:
            # Attach age to all patients from their health records (column E)
            try:
                records_res = supabase.table('records').select('patient_id, E').order('id', desc=False).execute()
                age_map = {}
                for r in (records_res.data or []):
                    pid = r.get('patient_id')
                    age = r.get('E')
                    if pid and age is not None:
                        try:
                            age_map[pid] = int(age)
                        except:
                            age_map[pid] = age
                for p in patients:
                    p['age'] = age_map.get(p['id'], 0)
            except Exception as re:
                print(f"Error fetching record ages for patients: {re}")
                for p in patients:
                    p.setdefault('age', 0)
        return patients
    except Exception as e:
        print(f"Error getting patients: {e}")
        return []

def get_patient_by_id(patient_id):
    if supabase is None:
        return None
    try:
        response = supabase.table('patients').select('*').eq('id', patient_id).execute()
        if response.data:
            patient = response.data[0]
            # Resolve age from latest record (column E)
            try:
                records = supabase.table('records').select('E').eq('patient_id', patient_id).order('id', desc=True).limit(1).execute()
                if records.data and records.data[0].get('E') is not None:
                    try:
                        patient['age'] = int(records.data[0]['E'])
                    except:
                        patient['age'] = records.data[0]['E']
                else:
                    patient['age'] = 0
            except Exception:
                patient['age'] = 0
            return patient
        return None
    except Exception as e:
        print(f"Error getting patient by id: {e}")
        return None

def add_patient(patient_data):
    if supabase is None:
        return None
    try:
        clean_patient = {
            "first_name": patient_data.get("first_name", "").strip(),
            "last_name": patient_data.get("last_name", "").strip(),
            "gender": patient_data.get("gender", "Not specified"),
            "contact_no": patient_data.get("contact_no", ""),
            "barangay": patient_data.get("barangay", "")
        }
        if "id" in patient_data and patient_data["id"]:
            clean_patient["id"] = int(patient_data["id"])

        response = supabase.table('patients').insert(clean_patient).execute()
        if response.data:
            return response.data[0]['id']
        return clean_patient.get('id')
    except Exception as e:
        print(f"Error adding patient: {e}")
        return None

def update_patient(patient_id, patient_data):
    if supabase is None:
        return False
    try:
        clean_data = {k: v for k, v in patient_data.items() if k not in ('id', 'birth_date')}
        response = supabase.table('patients').update(clean_data).eq('id', patient_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error updating patient: {e}")
        return False

def delete_patient(patient_id):
    if supabase is None:
        return False
    try:
        supabase.table('records').delete().eq('patient_id', patient_id).execute()
        response = supabase.table('patients').delete().eq('id', patient_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error deleting patient: {e}")
        return False

def get_records():
    if supabase is None:
        return []
    try:
        response = supabase.table('records').select('*').order('id', desc=False).execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting records: {e}")
        return []

def get_records_for_patient(patient_id):
    if supabase is None:
        return []
    try:
        response = supabase.table('records').select('*').eq('patient_id', patient_id).order('id', desc=False).execute()
        return response.data or []
    except Exception as e:
        print(f"Error getting records for patient: {e}")
        return []

def add_record(record_data):
    if supabase is None:
        return None
    try:
        clean_record = {
            "patient_id": int(record_data.get("patient_id", 1)),
            "A": record_data.get("A", datetime.now().strftime("%Y-%m-%d")),
            "B": record_data.get("B", datetime.now().strftime("%I:%M %p")),
            "C": record_data.get("C", ""),
            "D": record_data.get("D", ""),
            "E": int(record_data.get("E", 0)),
            "F": record_data.get("F", ""),
            "G": str(record_data.get("G", "0/0")),
            "H": int(record_data.get("H", 0)),
            "I": int(record_data.get("I", 0)),
            "J": float(record_data.get("J", 0.0)),
            "K": float(record_data.get("K", 0.0)),
            "L": float(record_data.get("L", 0.0)),
            "M": float(record_data.get("M", 0.0)),
            "bmi_category": record_data.get("bmi_category", "Normal"),
            "status": record_data.get("status", "Normal"),
            "remarks": record_data.get("remarks", ""),
            "created_at": record_data.get("created_at", datetime.now().strftime("%Y-%m-%d %I:%M %p"))
        }
        if "id" in record_data and record_data["id"]:
            clean_record["id"] = int(record_data["id"])

        response = supabase.table('records').insert(clean_record).execute()
        if response.data:
            return response.data[0]['id']
        return clean_record.get('id')
    except Exception as e:
        print(f"Error adding record: {e}")
        return None

def get_admin_users():
    if supabase is None:
        return []
    try:
        response = supabase.table('admin_users').select('*').execute()
        return response.data
    except Exception as e:
        print(f"Error getting admin users: {e}")
        return []

def get_admin_by_username(username):
    if supabase is None:
        return None
    try:
        response = supabase.table('admin_users').select('*').eq('username', username.lower()).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting admin by username: {e}")
        return None

def get_admin_by_id(admin_id):
    if supabase is None:
        return None
    try:
        response = supabase.table('admin_users').select('*').eq('id', admin_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting admin by id: {e}")
        return None

def add_admin_user(user_data):
    if supabase is None:
        return None
    try:
        response = supabase.table('admin_users').insert(user_data).execute()
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        print(f"Error adding admin user: {e}")
        return None

def update_admin_user(admin_id, user_data):
    if supabase is None:
        return False
    try:
        response = supabase.table('admin_users').update(user_data).eq('id', admin_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error updating admin user: {e}")
        return False

def delete_admin_user(admin_id):
    if supabase is None:
        return False
    try:
        response = supabase.table('admin_users').delete().eq('id', admin_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error deleting admin user: {e}")
        return False

def get_access_logs():
    if supabase is None:
        return []
    try:
        response = supabase.table('access_logs').select('*').order('date_time', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error getting access logs: {e}")
        return []

def add_access_log(user, role, action):
    if supabase is None:
        return None
    try:
        log_data = {
            "user": user,
            "role": role,
            "action": action,
            "date_time": datetime.now().strftime("%Y-%m-%d %I:%M %p")
        }
        response = supabase.table('access_logs').insert(log_data).execute()
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        print(f"Error adding access log: {e}")
        return None

def get_next_patient_id():
    patients = get_patients()
    if not patients:
        return 1
    return max(patient['id'] for patient in patients) + 1

def get_next_record_id():
    records = get_records()
    if not records:
        return 1
    return max(record['id'] for record in records) + 1

def get_next_admin_id():
    admin_users = get_admin_users()
    if not admin_users:
        return 1
    return max(user['id'] for user in admin_users) + 1


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def calculate_bmi(height_cm, weight_kg):
    if height_cm <= 0:
        return 0

    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 1)


def calculate_age(birth_date):
    if not birth_date:
        return 0
    if isinstance(birth_date, int):
        if 0 < birth_date < 130:
            return birth_date
        if 1900 <= birth_date <= datetime.now().year:
            return datetime.now().year - birth_date

    birth_str = str(birth_date).strip()
    if not birth_str:
        return 0

    if birth_str.isdigit() and len(birth_str) <= 3:
        val = int(birth_str)
        if 0 < val < 130:
            return val

    if birth_str.isdigit() and len(birth_str) == 4:
        val = int(birth_str)
        if 1900 <= val <= datetime.now().year:
            return datetime.now().year - val

    date_formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    if "T" in birth_str:
        birth_str = birth_str.split("T")[0]

    today = datetime.now()
    for fmt in date_formats:
        try:
            birth = datetime.strptime(birth_str, fmt)
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            if age >= 0:
                return age
        except (ValueError, TypeError):
            continue

    return 0


def get_bmi_category(bmi):
    if bmi <= 0:
        return "Invalid"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def get_detailed_status(temperature, heart_rate, oxygen_saturation, systolic, diastolic, bmi):
    issues = []

    # Check temperature
    if temperature > 37.5:
        issues.append("High Temp")

    # Check heart rate
    if heart_rate > 100:
        issues.append("High HR")
    elif heart_rate < 60:
        issues.append("Low HR")

    # Check oxygen saturation
    if oxygen_saturation < 95:
        issues.append("Low SpO2")

    # Check blood pressure
    if systolic > 140 or diastolic > 90:
        issues.append("High BP")
    elif systolic < 90 or diastolic < 60:
        issues.append("Low BP")

    # Check BMI
    bmi_cat = get_bmi_category(bmi)
    if bmi_cat != "Normal":
        issues.append(bmi_cat)

    # If no issues, return "Normal"
    if not issues:
        return "Normal"

    # If there are issues, return them as comma-separated list
    return ", ".join(issues)


def get_record_status(temperature, heart_rate, oxygen_saturation, systolic, diastolic, bmi_category):
    abnormal_vitals = (
        temperature > 37.5 or
        heart_rate < 60 or heart_rate > 100 or
        oxygen_saturation < 95 or
        systolic >= 140 or
        diastolic >= 90
    )

    abnormal_bmi = bmi_category in ["Underweight", "Overweight", "Obese"]

    if abnormal_vitals or abnormal_bmi:
        return "Needs Attention"

    return "Normal"


def get_patient_name(patient_id):
    patient = get_patient_by_id(patient_id)
    if patient:
        return f'{patient["first_name"]} {patient["last_name"]}'
    return "Unknown Patient"


def create_health_record(patient_id, temperature, heart_rate, oxygen_saturation, systolic, diastolic, height, weight, age=None):
    bmi = calculate_bmi(height, weight)
    bmi_category = get_bmi_category(bmi)

    status = get_detailed_status(temperature, heart_rate, oxygen_saturation, systolic, diastolic, bmi)

    abnormal_reasons = []

    if temperature > 37.5:
        abnormal_reasons.append("high body temperature")

    if heart_rate < 60:
        abnormal_reasons.append("low heart rate")

    if heart_rate > 100:
        abnormal_reasons.append("high heart rate")

    if oxygen_saturation < 95:
        abnormal_reasons.append("low oxygen saturation")

    if systolic >= 140 or diastolic >= 90:
        abnormal_reasons.append("high blood pressure")

    if bmi_category == "Underweight":
        abnormal_reasons.append("underweight BMI")

    if bmi_category == "Overweight":
        abnormal_reasons.append("overweight BMI")

    if bmi_category == "Obese":
        abnormal_reasons.append("obese BMI")

    if status != "Normal":
        remarks = "Needs health personnel review due to " + ", ".join(abnormal_reasons) + "."
    else:
        remarks = "Vital signs and BMI are within normal range."

    patient = get_patient_by_id(patient_id)
    if age is None or age == 0:
        age = patient.get("age", 0) if patient else 0

    new_record = {
        "id": get_next_record_id(),
        "patient_id": patient_id,
        "A": datetime.now().strftime("%Y-%m-%d"),  # Date
        "B": datetime.now().strftime("%I:%M %p"),  # Time
        "C": patient["first_name"] if patient else "",  # FirstName
        "D": patient["last_name"] if patient else "",  # LastName
        "E": age,  # Age
        "F": patient["gender"] if patient else "",  # Gender
        "G": f"{systolic}/{diastolic}",  # BloodPressure
        "H": heart_rate,  # HeartRate_BPM
        "I": oxygen_saturation,  # OxygenSaturation_pct
        "J": temperature,  # BodyTemp_C
        "K": weight,  # Weight_kg
        "L": height,  # Height_cm
        "M": bmi,  # BMI
        "bmi_category": bmi_category,
        "status": status,
        "remarks": remarks,
        "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }

    record_id = add_record(new_record)
    if record_id:
        new_record["id"] = record_id
    return new_record


WELLBEING_SURVEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wellbeing_surveys.json")


def load_wellbeing_surveys():
    if not os.path.exists(WELLBEING_SURVEY_FILE):
        return {}
    try:
        with open(WELLBEING_SURVEY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error loading wellbeing surveys: {e}")
        return {}


def get_wellbeing_survey(patient_id, record_id=None, record=None):
    # Check if survey_data is already stored on the record object from Supabase
    if record and isinstance(record.get("survey_data"), dict) and record["survey_data"]:
        return record["survey_data"]

    surveys = load_wellbeing_surveys()
    if record_id and f"record_{record_id}" in surveys:
        return surveys[f"record_{record_id}"]
    if f"patient_{patient_id}" in surveys:
        return surveys[f"patient_{patient_id}"]
    return None


def save_wellbeing_survey(patient_id, record_id, survey_data):
    surveys = load_wellbeing_surveys()
    payload = {
        "sleep": survey_data.get("sleep", "7_to_8"),
        "activity": survey_data.get("activity", "moderate"),
        "stress": survey_data.get("stress", "low"),
        "hydration_diet": survey_data.get("hydration_diet", "good"),
        "symptoms": survey_data.get("symptoms", "none"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }
    if record_id:
        surveys[f"record_{record_id}"] = payload
    surveys[f"patient_{patient_id}"] = payload

    try:
        with open(WELLBEING_SURVEY_FILE, "w", encoding="utf-8") as f:
            json.dump(surveys, f, indent=2)
    except Exception as e:
        print(f"Error saving wellbeing survey file: {e}")

    # Also attempt to persist in Supabase records.survey_data if column exists
    if supabase is not None and record_id:
        try:
            supabase.table("records").update({"survey_data": payload}).eq("id", record_id).execute()
        except Exception:
            pass

    return payload


def get_wellbeing_assessment(record, patient, survey=None):
    """
    Computes comprehensive, personalized wellbeing guidance based on collected screening vitals
    and optional 5-question patient lifestyle survey responses.
    Designed to support general health monitoring without providing medical diagnoses or treatment recommendations.
    """
    if not record:
        return None

    if survey is None and patient:
        survey = get_wellbeing_survey(patient.get("id"), record.get("id"), record)

    has_survey = bool(survey and isinstance(survey, dict) and survey.get("sleep"))

    sleep_ans = survey.get("sleep", "") if has_survey else ""
    activity_ans = survey.get("activity", "") if has_survey else ""
    stress_ans = survey.get("stress", "") if has_survey else ""
    diet_ans = survey.get("hydration_diet", "") if has_survey else ""
    symptom_ans = survey.get("symptoms", "") if has_survey else ""

    try:
        temp = float(record.get("J") or 0.0)
    except:
        temp = 0.0

    bp_str = str(record.get("G") or "120/80")
    try:
        bp_parts = bp_str.split("/")
        systolic = int(bp_parts[0]) if len(bp_parts) > 0 else 120
        diastolic = int(bp_parts[1]) if len(bp_parts) > 1 else 80
    except:
        systolic, diastolic = 120, 80

    try:
        hr = int(record.get("H") or 0)
    except:
        hr = 0

    try:
        spo2 = int(record.get("I") or 0)
    except:
        spo2 = 0

    try:
        weight = float(record.get("K") or 0.0)
    except:
        weight = 0.0

    try:
        height = float(record.get("L") or 0.0)
    except:
        height = 0.0

    try:
        bmi = float(record.get("M") or 0.0)
    except:
        bmi = 0.0

    if bmi == 0.0 and height > 0 and weight > 0:
        bmi = calculate_bmi(height, weight)

    bmi_cat = record.get("bmi_category") or get_bmi_category(bmi)

    # 1. Temperature Analysis (Personalized with hydration & symptom survey data)
    if temp > 37.5:
        temp_status = "Elevated"
        temp_badge = "badge-danger"
        temp_note = f"{temp:.1f}°C is above typical resting levels (36.0°C - 37.5°C)."
        if has_survey and diet_ans == "poor":
            temp_tips = "Since you reported low daily water intake (<4 glasses), prioritize immediate oral hydration with cool water or electrolyte fluids and rest in a cool room."
        elif has_survey and symptom_ans in ["aches_pains", "fatigue"]:
            temp_tips = "Elevated temperature paired with your reported body discomfort/fatigue warrants rest, plenty of fluids, and clinical monitoring."
        else:
            temp_tips = "Drink plenty of cool fluids, rest in a well-ventilated space, and re-check temperature regularly."
    elif temp < 36.0 and temp > 0:
        temp_status = "Below Average"
        temp_badge = "badge-warning"
        temp_note = f"{temp:.1f}°C is slightly below the standard baseline."
        temp_tips = "Keep warm with suitable clothing, consume warm nourishing beverages, and monitor if fatigue persists."
    else:
        temp_status = "Normal"
        temp_badge = "badge-success"
        temp_note = f"{temp:.1f}°C is within optimal standard resting body temperature."
        if has_survey and diet_ans == "poor":
            temp_tips = "Temperature is normal, though increasing your water intake from <4 glasses to 8+ glasses will help sustain thermal and cellular balance."
        else:
            temp_tips = "Continue normal daily hydration and thermal comfort habits."

    # 2. Blood Pressure Analysis (Personalized with stress, diet & activity survey data)
    if systolic >= 140 or diastolic >= 90:
        bp_status = "High BP (Stage 2)"
        bp_badge = "badge-danger"
        bp_note = f"{bp_str} mmHg is in the hypertension range."
        if has_survey and stress_ans == "high" and diet_ans == "poor":
            bp_tips = "Your reported High Daily Stress and high-sodium/low-water diet directly impact blood pressure. Prioritize immediate sodium reduction, guided breathing, and a physician review."
        elif has_survey and stress_ans == "high":
            bp_tips = "High daily stress can spike blood pressure. Practice 10 minutes of slow diaphragmatic breathing, reduce workload tension, and have clinic staff review this reading."
        elif has_survey and diet_ans == "poor":
            bp_tips = "Cut back on processed/salty foods you reported, increase water intake to 8+ glasses, and consult a healthcare provider regarding this reading."
        else:
            bp_tips = "Limit dietary sodium, practice slow diaphragmatic breathing, and have your blood pressure reviewed by a healthcare professional."
    elif systolic >= 130 or diastolic >= 80:
        bp_status = "Stage 1 Elevated"
        bp_badge = "badge-warning"
        bp_note = f"{bp_str} mmHg is slightly above standard normal parameters."
        if has_survey and stress_ans in ["high", "moderate"]:
            bp_tips = f"With your {stress_ans} stress level, daily mindfulness breaks, 7-8 hours of sleep, and cutting excess salt can help bring {bp_str} mmHg back under 120/80."
        elif has_survey and activity_ans == "sedentary":
            bp_tips = "Transitioning from a sedentary routine to a 20-minute daily brisk walk is one of the most effective ways to naturally lower Stage 1 elevated BP."
        else:
            bp_tips = "Engage in moderate physical activity like walking, manage daily stress, and drink adequate water throughout the day."
    elif systolic < 90 or diastolic < 60:
        bp_status = "Low BP"
        bp_badge = "badge-info"
        bp_note = f"{bp_str} mmHg is lower than standard resting range."
        if has_survey and symptom_ans == "headache_dizziness":
            bp_tips = "Because you also reported dizziness/headaches with low BP, increase fluid intake immediately, stand up slowly, and notify clinic staff."
        else:
            bp_tips = "Stay hydrated, stand up slowly after sitting or resting, and consult a provider if dizziness occurs."
    else:
        bp_status = "Optimal"
        bp_badge = "badge-success"
        bp_note = f"{bp_str} mmHg is within healthy resting parameters."
        if has_survey and stress_ans == "high":
            bp_tips = "Your BP is currently optimal despite reporting high daily stress—protect your cardiovascular health with daily relaxation breaks so stress doesn't elevate it over time."
        else:
            bp_tips = "Maintain a heart-healthy diet with plenty of potassium-rich foods and regular movement."

    # 3. Heart Rate Analysis (Personalized with sleep, stress & activity survey data)
    if hr > 100:
        hr_status = "Elevated Pulse"
        hr_badge = "badge-danger"
        hr_note = f"{hr} BPM is elevated for a resting heart rate."
        if has_survey and (stress_ans == "high" or sleep_ans in ["under_5", "5_to_6"]):
            hr_tips = "Insufficient sleep and elevated stress activate the sympathetic nervous system, raising resting pulse. Prioritize rest, hydration, and reduced caffeine today."
        else:
            hr_tips = "Allow time for physical and mental relaxation; reduce caffeine and stimulant intake."
    elif hr < 60 and hr > 0:
        hr_status = "Low Pulse"
        hr_badge = "badge-warning"
        hr_note = f"{hr} BPM is lower than average (unless physically conditioned or an athlete)."
        if has_survey and activity_ans == "active":
            hr_tips = "Since you exercise 5+ days/week, a lower resting heart rate often reflects strong cardiovascular conditioning. Monitor only if dizziness or fatigue occurs."
        else:
            hr_tips = "Ensure adequate rest and hydration; note if any fatigue or lightheadedness occurs."
    else:
        hr_status = "Normal Pulse"
        hr_badge = "badge-success"
        hr_note = f"{hr} BPM is within the healthy resting pulse range (60-100 BPM)."
        if has_survey and activity_ans in ["sedentary", "light"]:
            hr_tips = "Your resting pulse is normal. Adding 2–3 days of moderate cardio weekly will further strengthen heart rate variability and stamina."
        else:
            hr_tips = "Support cardiorespiratory endurance through consistent aerobic movement."

    # 4. Oxygen Saturation Analysis (Personalized with breathing discomfort & activity)
    if spo2 < 95 and spo2 > 0:
        spo2_status = "Low Oxygen"
        spo2_badge = "badge-danger"
        spo2_note = f"{spo2}% is below optimal arterial oxygen saturation (≥95%)."
        if has_survey and symptom_ans == "shortness_breath":
            spo2_tips = "You reported shortness of breath alongside low SpO2 (<95%). Sit upright, breathe slowly, and have a healthcare provider evaluate you promptly."
        else:
            spo2_tips = "Sit upright, practice relaxed slow deep breathing, and have your oxygenation evaluated by clinic staff."
    else:
        spo2_status = "Normal Saturation"
        spo2_badge = "badge-success"
        spo2_note = f"{spo2}% indicates efficient respiratory oxygen delivery."
        if has_survey and symptom_ans == "shortness_breath":
            spo2_tips = "Resting SpO2 is normal (≥95%), though since you noted mild breathlessness on exertion, pace your physical activities and discuss respiratory conditioning with staff."
        else:
            spo2_tips = "Maintain good indoor air ventilation and practice regular aerobic exercise."

    # 5. BMI & Weight Analysis (Personalized with activity & nutrition survey data)
    if bmi_cat == "Underweight":
        bmi_status = "Underweight"
        bmi_badge = "badge-info"
        bmi_note = f"BMI of {bmi:.1f} kg/m² is below the healthy weight threshold (<18.5)."
        if has_survey and diet_ans in ["poor", "fair"]:
            bmi_tips = "Based on your nutrition survey, add calorie-dense whole foods (avocados, nuts, eggs, lean proteins) and structured meal times to build healthy mass."
        else:
            bmi_tips = "Focus on nutrient-rich whole foods, healthy fats, and balanced caloric intake."
    elif bmi_cat in ["Overweight", "Obese"]:
        bmi_status = bmi_cat
        bmi_badge = "badge-warning" if bmi_cat == "Overweight" else "badge-danger"
        bmi_note = f"BMI of {bmi:.1f} kg/m² is in the {bmi_cat.lower()} category (≥25.0)."
        if has_survey and activity_ans == "sedentary":
            bmi_tips = f"Since your current routine is mostly sedentary, start gently with a 15–20 minute daily walk and replace sugary beverages with water to steadily improve your {bmi:.1f} BMI."
        elif has_survey and diet_ans == "poor":
            bmi_tips = "Pairing your current movement habits with whole, high-fiber foods and 8+ glasses of water before meals will significantly support healthy weight management."
        else:
            bmi_tips = "Incorporate 30 minutes of daily physical activity, increase dietary fiber, and balance portion sizes."
    else:
        bmi_status = "Normal Weight"
        bmi_badge = "badge-success"
        bmi_note = f"BMI of {bmi:.1f} kg/m² is in the ideal healthy weight bracket (18.5 - 24.9)."
        if has_survey and activity_ans == "active" and diet_ans == "good":
            bmi_tips = "Your active exercise routine and balanced nutrition are keeping your BMI in the ideal range—keep up these strong habits!"
        else:
            bmi_tips = "Keep up a balanced nutritional regimen and consistent weekly exercise."

    # Overall wellness findings & composite score
    findings = []
    if temp_status != "Normal": findings.append("Body Temperature")
    if "Normal" not in bp_status and "Optimal" not in bp_status: findings.append("Blood Pressure")
    if "Normal" not in hr_status: findings.append("Heart Rate")
    if "Normal" not in spo2_status: findings.append("Oxygen Saturation")
    if bmi_cat != "Normal": findings.append("BMI / Body Composition")

    # Calculate Vitals Score (max 60)
    vitals_score = 60 - (len(findings) * 10)
    if "danger" in [temp_badge, bp_badge, hr_badge, spo2_badge, bmi_badge]:
        vitals_score -= 5
    vitals_score = max(15, min(60, vitals_score))

    # Build Survey Profile & Lifestyle Score (max 40)
    survey_items = []
    lifestyle_watchpoints = []
    lifestyle_score = 0

    if has_survey:
        # Q1: Sleep
        sleep_map = {
            "under_5": ("< 5 Hours / Night", "Sleep Deficit", "badge-danger", 2),
            "5_to_6": ("5 – 6 Hours / Night", "Below Ideal", "badge-warning", 5),
            "7_to_8": ("7 – 8 Hours / Night", "Optimal Rest", "badge-success", 8),
            "over_9": ("9+ Hours / Night", "Extended Sleep", "badge-info", 6)
        }
        s_val, s_status, s_badge, s_pts = sleep_map.get(sleep_ans, ("7 – 8 Hours / Night", "Optimal Rest", "badge-success", 8))
        lifestyle_score += s_pts
        if s_badge in ["badge-danger", "badge-warning"]:
            lifestyle_watchpoints.append("Sleep Duration")
        survey_items.append({
            "icon": "😴",
            "label": "Nightly Sleep",
            "value": s_val,
            "status": s_status,
            "badge": s_badge
        })

        # Q2: Physical Activity
        act_map = {
            "sedentary": ("Rarely / Sedentary", "Low Activity", "badge-danger", 2),
            "light": ("1 – 2 Days / Week", "Light Movement", "badge-warning", 5),
            "moderate": ("3 – 4 Days / Week", "Moderately Active", "badge-success", 8),
            "active": ("5+ Days / Week", "Highly Active", "badge-success", 8)
        }
        a_val, a_status, a_badge, a_pts = act_map.get(activity_ans, ("3 – 4 Days / Week", "Moderately Active", "badge-success", 8))
        lifestyle_score += a_pts
        if a_badge in ["badge-danger", "badge-warning"]:
            lifestyle_watchpoints.append("Physical Activity")
        survey_items.append({
            "icon": "🏃",
            "label": "Exercise Routine",
            "value": a_val,
            "status": a_status,
            "badge": a_badge
        })

        # Q3: Daily Stress
        stress_map = {
            "low": ("Low / Relaxed", "Well Managed", "badge-success", 8),
            "moderate": ("Moderate Pressure", "Manageable", "badge-warning", 5),
            "high": ("High / Overwhelmed", "Elevated Stress", "badge-danger", 2)
        }
        st_val, st_status, st_badge, st_pts = stress_map.get(stress_ans, ("Low / Relaxed", "Well Managed", "badge-success", 8))
        lifestyle_score += st_pts
        if st_badge == "badge-danger":
            lifestyle_watchpoints.append("High Daily Stress")
        survey_items.append({
            "icon": "🧠",
            "label": "Daily Stress Level",
            "value": st_val,
            "status": st_status,
            "badge": st_badge
        })

        # Q4: Hydration & Diet
        diet_map = {
            "poor": ("< 4 Cups / Processed", "Needs Improvement", "badge-danger", 2),
            "fair": ("4 – 6 Cups / Mixed Diet", "Moderate Intake", "badge-warning", 5),
            "good": ("8+ Cups / Whole Foods", "Optimal Nutrition", "badge-success", 8)
        }
        d_val, d_status, d_badge, d_pts = diet_map.get(diet_ans, ("8+ Cups / Whole Foods", "Optimal Nutrition", "badge-success", 8))
        lifestyle_score += d_pts
        if d_badge in ["badge-danger", "badge-warning"]:
            lifestyle_watchpoints.append("Hydration & Nutrition")
        survey_items.append({
            "icon": "🥗",
            "label": "Hydration & Diet",
            "value": d_val,
            "status": d_status,
            "badge": d_badge
        })

        # Q5: Current Discomfort / Symptoms
        sym_map = {
            "none": ("No Discomfort", "Symptom-Free", "badge-success", 8),
            "fatigue": ("Frequent Fatigue / Low Energy", "Monitor Energy", "badge-warning", 4),
            "headache_dizziness": ("Headaches / Dizziness", "Clinical Watch", "badge-danger", 2),
            "shortness_breath": ("Breathlessness on Exertion", "Clinical Watch", "badge-danger", 2),
            "aches_pains": ("Muscle / Joint Aches", "Physical Strain", "badge-warning", 4)
        }
        sy_val, sy_status, sy_badge, sy_pts = sym_map.get(symptom_ans, ("No Discomfort", "Symptom-Free", "badge-success", 8))
        lifestyle_score += sy_pts
        if symptom_ans != "none":
            lifestyle_watchpoints.append(f"Reported {sy_val}")
        survey_items.append({
            "icon": "🩺",
            "label": "Reported Symptoms",
            "value": sy_val,
            "status": sy_status,
            "badge": sy_badge
        })

    wellbeing_score = (vitals_score + lifestyle_score) if has_survey else int((vitals_score / 60) * 100)

    # Overall Summary & Tier (Personalized if survey taken)
    all_watchpoints = findings + lifestyle_watchpoints
    if not findings and not lifestyle_watchpoints:
        overall_tier = "Optimal Wellbeing"
        tier_badge = "badge-success"
        if has_survey:
            overall_summary = (
                f"Personalized Well-Being Score: {wellbeing_score}/100. Both clinical vital signs and reported "
                "daily lifestyle habits (sleep, stress, hydration, and activity) are in healthy alignment."
            )
        else:
            overall_summary = "All vital signs and physical health metrics are within expected healthy reference ranges. Take the 5-question survey to unlock personalized lifestyle guidance."
    elif "danger" not in [temp_badge, bp_badge, hr_badge, spo2_badge] and len(findings) <= 2 and symptom_ans not in ["headache_dizziness", "shortness_breath"]:
        overall_tier = "General Wellness with Minor Watchpoints"
        tier_badge = "badge-warning"
        if has_survey:
            overall_summary = (
                f"Personalized Well-Being Score: {wellbeing_score}/100. Baseline vitals and survey responses highlight "
                f"focus areas in {', '.join(all_watchpoints[:4])}. Follow the tailored action plan below."
            )
        else:
            overall_summary = f"Most baseline metrics are stable, with {len(findings)} area(s) ({', '.join(findings)}) flagged for routine lifestyle attention and observation."
    else:
        overall_tier = "Clinical Attention Recommended"
        tier_badge = "badge-danger"
        if has_survey:
            overall_summary = (
                f"Personalized Well-Being Score: {wellbeing_score}/100. Screening vitals and questionnaire responses "
                f"flag {', '.join(all_watchpoints[:4])} for priority healthcare personnel review and lifestyle adjustment."
            )
        else:
            overall_summary = f"Screening results indicate {len(findings)} metric(s) ({', '.join(findings)}) outside optimal ranges. Healthcare personnel review is recommended."

    # Dynamic Personalized Guidance Pillars
    if has_survey:
        guidance_pillars = []

        # Pillar 1: Hydration & Nutrition (Tailored to Q4 + BP/BMI)
        if diet_ans == "poor":
            guidance_pillars.append({
                "icon": "💧",
                "title": "Priority Hydration & Low-Sodium Nutrition",
                "tag": "High Priority Focus",
                "tag_badge": "badge-danger",
                "personal_note": f"Tailored to your survey (<4 cups water/day & processed meals) and {bp_str} mmHg BP",
                "content": "Gradually step up your water intake by drinking 1 full glass upon waking and before every meal (targeting 8 glasses/day). Swap canned or salty snacks for potassium-rich local produce (bananas, leafy greens) to support blood pressure and kidney health."
            })
        elif diet_ans == "fair":
            guidance_pillars.append({
                "icon": "🥗",
                "title": "Stepping Up Daily Hydration & Whole Foods",
                "tag": "Recommended Adjustment",
                "tag_badge": "badge-warning",
                "personal_note": f"Tailored to your moderate intake (4–6 cups/day) and BMI of {bmi:.1f} kg/m²",
                "content": "You are halfway to optimal hydration—carry a reusable water bottle to add 2–3 more glasses daily. Fill half your plate with fiber-rich vegetables and lean proteins to sustain steady energy levels."
            })
        else:
            guidance_pillars.append({
                "icon": "🥗",
                "title": "Sustaining Optimal Nutrition & Hydration",
                "tag": "Healthy Habit",
                "tag_badge": "badge-success",
                "personal_note": "Tailored to your strong 8+ glasses water intake and balanced meal routine",
                "content": "Your consistent hydration and whole-food nutrition provide a strong metabolic foundation. Continue limiting refined sugars and excess sodium to protect long-term vascular health."
            })

        # Pillar 2: Physical Activity (Tailored to Q2 + BMI/HR)
        if activity_ans == "sedentary":
            guidance_pillars.append({
                "icon": "🏃",
                "title": "Gentle Active Movement Starter Plan",
                "tag": "High Priority Focus",
                "tag_badge": "badge-danger",
                "personal_note": f"Tailored to your sedentary routine and {bmi:.1f} kg/m² BMI ({bmi_status})",
                "content": "Avoid intense workouts right away—start with a realistic 15-minute brisk walk after meals 4 days a week, plus 2-minute standing stretch breaks every hour of sitting to boost circulation and metabolism."
            })
        elif activity_ans == "light":
            guidance_pillars.append({
                "icon": "🏃",
                "title": "Building Cardiorespiratory Consistency",
                "tag": "Recommended Adjustment",
                "tag_badge": "badge-warning",
                "personal_note": f"Tailored to your 1–2 days/week light activity and {hr} BPM heart rate",
                "content": "Add 1 to 2 extra days of 30-minute moderate aerobic activity (brisk walking, cycling, or dancing) to reach the recommended 150 weekly minutes for heart and metabolic conditioning."
            })
        else:
            guidance_pillars.append({
                "icon": "🏃",
                "title": "Active Fitness & Recovery Balance",
                "tag": "Healthy Habit",
                "tag_badge": "badge-success",
                "personal_note": "Tailored to your active weekly exercise schedule (3+ days/week)",
                "content": "Your regular physical activity strongly supports cardiovascular endurance and weight stability. Pair your workouts with proper warm-ups, mobility stretching, and post-exercise electrolyte hydration."
            })

        # Pillar 3: Sleep & Energy Recovery (Tailored to Q1 + Q5 Fatigue/HR)
        if sleep_ans in ["under_5", "5_to_6"]:
            guidance_pillars.append({
                "icon": "😴",
                "title": "Sleep Debt Recovery & Circadian Reset",
                "tag": "High Priority Focus" if sleep_ans == "under_5" else "Recommended Adjustment",
                "tag_badge": "badge-danger" if sleep_ans == "under_5" else "badge-warning",
                "personal_note": f"Tailored to your reported {'<5' if sleep_ans == 'under_5' else '5–6'} hours of nightly sleep",
                "content": "Short sleep elevates cortisol, blood pressure, and daytime fatigue. Set a fixed wind-down alarm 45 minutes before bed, dim phone screens, and avoid caffeine after 2:00 PM to extend restful sleep toward 7–8 hours."
            })
        else:
            guidance_pillars.append({
                "icon": "😴",
                "title": "Restorative Sleep Maintenance",
                "tag": "Healthy Habit",
                "tag_badge": "badge-success",
                "personal_note": "Tailored to your restorative nightly sleep schedule",
                "content": "Your sleep duration supports cellular repair, immune resilience, and hormonal balance. Keep your waking and sleeping times consistent even on weekends."
            })

        # Pillar 4: Stress & Symptom Management (Tailored to Q3 + Q5 + BP)
        if stress_ans == "high" or symptom_ans != "none":
            sym_label = {
                "none": "elevated daily stress",
                "fatigue": "frequent fatigue",
                "headache_dizziness": "headaches/dizziness",
                "shortness_breath": "breathlessness on exertion",
                "aches_pains": "muscle/joint aches"
            }.get(symptom_ans, "reported symptoms")
            guidance_pillars.append({
                "icon": "🧘",
                "title": "Stress Regulation & Symptom Care",
                "tag": "High Priority Focus" if (stress_ans == "high" or symptom_ans in ["headache_dizziness", "shortness_breath"]) else "Recommended Adjustment",
                "tag_badge": "badge-danger" if (stress_ans == "high" or symptom_ans in ["headache_dizziness", "shortness_breath"]) else "badge-warning",
                "personal_note": f"Tailored to your {stress_ans} stress level and {sym_label}",
                "content": "Practice 5 minutes of box breathing (inhale 4s, hold 4s, exhale 4s) twice daily to calm nervous system tension. Pace your physical workload, track when discomfort occurs, and share these notes with clinic staff."
            })
        else:
            guidance_pillars.append({
                "icon": "🧘",
                "title": "Mental & Emotional Equilibrium",
                "tag": "Healthy Habit",
                "tag_badge": "badge-success",
                "personal_note": "Tailored to your low stress level and symptom-free status",
                "content": "You reported manageable daily stress and no physical discomfort. Continue setting healthy work-life boundaries, spending time outdoors, and staying connected with community support."
            })
    else:
        guidance_pillars = [
            {
                "icon": "💧",
                "title": "Hydration Balance",
                "tag": "General Guidance",
                "tag_badge": "badge-info",
                "personal_note": "Complete the 5-question survey to personalize this pillar",
                "content": "Aim for 8 to 10 glasses (approx. 2 liters) of clean water daily. Hydration stabilizes cellular function, supports healthy blood viscosity, and maintains normal body temperature."
            },
            {
                "icon": "🥗",
                "title": "Wholesome Nutrition",
                "tag": "General Guidance",
                "tag_badge": "badge-info",
                "personal_note": "Complete the 5-question survey to personalize this pillar",
                "content": "Prioritize fiber-rich vegetables, fresh fruits, whole grains, and lean proteins. Limit high-sodium processed foods and refined sugars to promote cardiovascular and metabolic health."
            },
            {
                "icon": "🏃",
                "title": "Active Movement",
                "tag": "General Guidance",
                "tag_badge": "badge-info",
                "personal_note": "Complete the 5-question survey to personalize this pillar",
                "content": "Engage in 150 minutes of moderate aerobic activity weekly (such as brisk walking, light cycling, or swimming) paired with daily mobility stretching."
            },
            {
                "icon": "😴",
                "title": "Restorative Sleep",
                "tag": "General Guidance",
                "tag_badge": "badge-info",
                "personal_note": "Complete the 5-question survey to personalize this pillar",
                "content": "Ensure 7 to 9 hours of uninterrupted sleep each night. Consistent sleep schedules optimize immune response, regulate cortisol levels, and support cardiovascular stability."
            }
        ]

    return {
        "has_survey": has_survey,
        "survey": survey or {},
        "survey_items": survey_items,
        "wellbeing_score": wellbeing_score,
        "overall_tier": overall_tier,
        "tier_badge": tier_badge,
        "overall_summary": overall_summary,
        "findings": findings,
        "disclaimer": (
            "The Current Well Being Assessment feature has been added to support the monitoring "
            "of users' general health and wellness. This feature considers collected health information "
            "and provides general wellness guidance to help users better understand their screening results. "
            "It is designed to support health monitoring without providing medical diagnoses or treatment recommendations."
        ),
        "vitals": [
            {
                "name": "Body Temperature",
                "icon": "🌡️",
                "value": f"{temp:.1f} °C",
                "status": temp_status,
                "badge": temp_badge,
                "note": temp_note,
                "tips": temp_tips,
                "reference": "36.0 °C – 37.5 °C"
            },
            {
                "name": "Blood Pressure",
                "icon": "🩺",
                "value": f"{bp_str} mmHg",
                "status": bp_status,
                "badge": bp_badge,
                "note": bp_note,
                "tips": bp_tips,
                "reference": "<120 / <80 mmHg"
            },
            {
                "name": "Heart Rate",
                "icon": "❤️",
                "value": f"{hr} BPM",
                "status": hr_status,
                "badge": hr_badge,
                "note": hr_note,
                "tips": hr_tips,
                "reference": "60 – 100 BPM"
            },
            {
                "name": "Oxygen Saturation",
                "icon": "💧",
                "value": f"{spo2}% SpO2",
                "status": spo2_status,
                "badge": spo2_badge,
                "note": spo2_note,
                "tips": spo2_tips,
                "reference": "≥ 95%"
            },
            {
                "name": "Body Mass Index",
                "icon": "⚖️",
                "value": f"{bmi:.1f} kg/m²",
                "status": bmi_status,
                "badge": bmi_badge,
                "note": bmi_note,
                "tips": bmi_tips,
                "reference": "18.5 – 24.9 (Normal)"
            }
        ],
        "guidance_pillars": guidance_pillars
    }


def dashboard_stats():
    patients_list = get_patients()
    records_list = get_records()

    total_patients = len(patients_list)
    total_records = len(records_list)

    # Count normal and attention records based on actual status from database
    normal_records = len([record for record in records_list if record["status"] == "Normal"])
    attention_records = len([record for record in records_list if record["status"] != "Normal"])

    if total_records > 0:
        average_bmi = round(sum(record["M"] for record in records_list if record.get("M")) / total_records, 1)
    else:
        average_bmi = 0

    return {
        "total_patients": total_patients,
        "total_records": total_records,
        "normal_records": normal_records,
        "attention_records": attention_records,
        "average_bmi": average_bmi,
        "documentation_reduction": 70
    }


def bmi_trends():
    records_list = get_records()
    labels = ["Underweight", "Normal", "Overweight", "Obese"]
    total = len(records_list) if records_list else 1
    trend_data = []

    for label in labels:
        count = len([record for record in records_list if record["bmi_category"] == label])
        percentage = round((count / total) * 100)

        trend_data.append({
            "label": label,
            "count": count,
            "percentage": percentage
        })

    return trend_data


def bmi_chart_records():
    records_list = get_records()
    return [
        {
            "bmi": record["M"],
            "category": record["bmi_category"],
            "created_at": record["created_at"],
            "patient_name": f"{record.get('C', '')} {record.get('D', '')}"
        }
        for record in records_list
    ]


def all_vitals_chart_records(records_list=None):
    if records_list is None:
        records_list = get_records()

    chart_data = []
    for record in records_list:
        # Blood pressure parse
        bp_val = str(record.get("G") or record.get("blood_pressure") or "").strip()
        systolic = 0
        diastolic = 0
        if "/" in bp_val:
            parts = bp_val.split("/")
            try:
                systolic = int(parts[0].strip())
                diastolic = int(parts[1].strip())
            except:
                systolic = 0
                diastolic = 0

        # BP Category
        if systolic >= 140 or diastolic >= 90:
            bp_cat = "High BP (Stage 2)"
        elif systolic >= 130 or diastolic >= 80:
            bp_cat = "Stage 1 Elevated"
        elif (systolic < 90 and systolic > 0) or (diastolic < 60 and diastolic > 0):
            bp_cat = "Low BP"
        elif systolic > 0 and diastolic > 0:
            bp_cat = "Optimal"
        else:
            bp_cat = "Unrecorded"

        # Heart rate
        try:
            hr = int(record.get("H") or record.get("heart_rate") or 0)
        except:
            hr = 0

        if hr > 100:
            hr_cat = "Tachycardia (>100 bpm)"
        elif hr < 60 and hr > 0:
            hr_cat = "Bradycardia (<60 bpm)"
        elif hr >= 60:
            hr_cat = "Normal (60-100 bpm)"
        else:
            hr_cat = "Unrecorded"

        # SpO2
        try:
            spo2 = int(record.get("I") or record.get("oxygen_saturation") or 0)
        except:
            spo2 = 0

        if spo2 >= 95:
            spo2_cat = "Normal (≥95%)"
        elif spo2 > 0:
            spo2_cat = "Low (<95% Hypoxia Risk)"
        else:
            spo2_cat = "Unrecorded"

        # Body Temperature
        try:
            temp = float(record.get("J") or record.get("temperature") or 0.0)
        except:
            temp = 0.0

        if temp > 37.5:
            temp_cat = "Elevated / Fever (>37.5°C)"
        elif temp < 36.0 and temp > 0:
            temp_cat = "Below Normal (<36.0°C)"
        elif temp >= 36.0:
            temp_cat = "Normal (36.0-37.5°C)"
        else:
            temp_cat = "Unrecorded"

        # Weight & Height
        try:
            weight = float(record.get("K") or record.get("weight") or 0.0)
        except:
            weight = 0.0

        try:
            height = float(record.get("L") or record.get("height") or 0.0)
        except:
            height = 0.0

        # BMI
        try:
            bmi = float(record.get("M") or record.get("bmi") or 0.0)
        except:
            bmi = 0.0

        if bmi == 0.0 and height > 0 and weight > 0:
            bmi = calculate_bmi(height, weight)

        patient_name = f"{record.get('C', '')} {record.get('D', '')}".strip()
        if not patient_name:
            patient_name = record.get("patient_name") or f"Patient #{record.get('patient_id', '')}"

        created_at_str = str(record.get("created_at") or "").strip()
        if not created_at_str:
            created_at_str = f"{record.get('A', '')} {record.get('B', '')}".strip()

        chart_data.append({
            "id": record.get("id"),
            "patient_id": record.get("patient_id"),
            "patient_name": patient_name,
            "created_at": created_at_str,
            "systolic": systolic,
            "diastolic": diastolic,
            "bp_str": f"{systolic}/{diastolic}" if systolic and diastolic else bp_val,
            "bp_category": bp_cat,
            "heart_rate": hr,
            "hr_category": hr_cat,
            "oxygen_saturation": spo2,
            "spo2_category": spo2_cat,
            "temperature": round(temp, 1),
            "temp_category": temp_cat,
            "weight": round(weight, 1),
            "height": round(height, 1),
            "bmi": round(bmi, 1),
            "bmi_category": record.get("bmi_category") or get_bmi_category(bmi),
            "status": record.get("status", "Normal"),
            "remarks": record.get("remarks", "")
        })

    return chart_data


def comprehensive_vitals_analytics(records_list=None):
    if records_list is None:
        records_list = get_records()

    total = len(records_list)
    if total == 0:
        return {
            "total_records": 0,
            "normal_count": 0,
            "attention_count": 0,
            "compliance_rate": 100,
            "bp": {
                "avg_sys": 0, "avg_dia": 0, "bp_str": "—",
                "min_sys": 0, "max_sys": 0, "min_dia": 0, "max_dia": 0,
                "optimal": 0, "optimal_pct": 0, "elevated": 0, "elevated_pct": 0,
                "stage2": 0, "stage2_pct": 0, "low": 0, "low_pct": 0, "hypertensive_pct": 0
            },
            "hr": {
                "avg": 0, "min": 0, "max": 0,
                "normal": 0, "normal_pct": 0, "tachycardia": 0, "tachycardia_pct": 0,
                "bradycardia": 0, "bradycardia_pct": 0, "flag_pct": 0
            },
            "spo2": {
                "avg": 0.0, "min": 0, "max": 0,
                "normal": 0, "normal_pct": 0, "low": 0, "risk_pct": 0
            },
            "temp": {
                "avg": 0.0, "min": 0.0, "max": 0.0,
                "normal": 0, "normal_pct": 0, "fever": 0, "fever_pct": 0, "low": 0, "low_pct": 0
            },
            "bmi": {
                "avg_bmi": 0.0, "avg_weight": 0.0, "avg_height": 0.0,
                "underweight": 0, "underweight_pct": 0,
                "normal": 0, "normal_pct": 0,
                "overweight": 0, "overweight_pct": 0,
                "obese": 0, "obese_pct": 0
            },
            "vital_risk_radar": []
        }

    parsed = all_vitals_chart_records(records_list)

    normal_cnt = len([r for r in parsed if r["status"] == "Normal"])
    attention_cnt = total - normal_cnt
    compliance_rate = round((normal_cnt / total) * 100, 1)

    # Blood Pressure Analytics
    sys_list = [r["systolic"] for r in parsed if r["systolic"] > 0]
    dia_list = [r["diastolic"] for r in parsed if r["diastolic"] > 0]
    avg_sys = round(sum(sys_list) / len(sys_list)) if sys_list else 0
    avg_dia = round(sum(dia_list) / len(dia_list)) if dia_list else 0
    min_sys = min(sys_list) if sys_list else 0
    max_sys = max(sys_list) if sys_list else 0
    min_dia = min(dia_list) if dia_list else 0
    max_dia = max(dia_list) if dia_list else 0

    bp_optimal = len([r for r in parsed if r["bp_category"] == "Optimal"])
    bp_elevated = len([r for r in parsed if r["bp_category"] == "Stage 1 Elevated"])
    bp_stage2 = len([r for r in parsed if r["bp_category"] == "High BP (Stage 2)"])
    bp_low = len([r for r in parsed if r["bp_category"] == "Low BP"])
    hypertensive_pct = round(((bp_elevated + bp_stage2) / total) * 100, 1)
    optimal_pct = round((bp_optimal / total) * 100, 1)

    # Heart Rate Analytics
    hr_list = [r["heart_rate"] for r in parsed if r["heart_rate"] > 0]
    avg_hr = round(sum(hr_list) / len(hr_list)) if hr_list else 0
    min_hr = min(hr_list) if hr_list else 0
    max_hr = max(hr_list) if hr_list else 0
    hr_normal = len([r for r in parsed if "Normal" in r["hr_category"]])
    hr_tachy = len([r for r in parsed if "Tachycardia" in r["hr_category"]])
    hr_brady = len([r for r in parsed if "Bradycardia" in r["hr_category"]])
    hr_normal_pct = round((hr_normal / total) * 100, 1)

    # SpO2 Analytics
    spo2_list = [r["oxygen_saturation"] for r in parsed if r["oxygen_saturation"] > 0]
    avg_spo2 = round(sum(spo2_list) / len(spo2_list), 1) if spo2_list else 0.0
    min_spo2 = min(spo2_list) if spo2_list else 0
    max_spo2 = max(spo2_list) if spo2_list else 0
    spo2_normal = len([r for r in parsed if "Normal" in r["spo2_category"]])
    spo2_low = len([r for r in parsed if "Low" in r["spo2_category"]])
    spo2_normal_pct = round((spo2_normal / total) * 100, 1)
    spo2_risk_pct = round((spo2_low / total) * 100, 1)

    # Temperature Analytics
    temp_list = [r["temperature"] for r in parsed if r["temperature"] > 0]
    avg_temp = round(sum(temp_list) / len(temp_list), 1) if temp_list else 0.0
    min_temp = min(temp_list) if temp_list else 0.0
    max_temp = max(temp_list) if temp_list else 0.0
    temp_normal = len([r for r in parsed if "Normal" in r["temp_category"]])
    temp_fever = len([r for r in parsed if "Elevated" in r["temp_category"]])
    temp_low = len([r for r in parsed if "Below Normal" in r["temp_category"]])
    temp_normal_pct = round((temp_normal / total) * 100, 1)
    temp_fever_pct = round((temp_fever / total) * 100, 1)

    # BMI & Weight Analytics
    bmi_list = [r["bmi"] for r in parsed if r["bmi"] > 0]
    weight_list = [r["weight"] for r in parsed if r["weight"] > 0]
    height_list = [r["height"] for r in parsed if r["height"] > 0]
    avg_bmi = round(sum(bmi_list) / len(bmi_list), 1) if bmi_list else 0.0
    avg_weight = round(sum(weight_list) / len(weight_list), 1) if weight_list else 0.0
    avg_height = round(sum(height_list) / len(height_list), 1) if height_list else 0.0
    bmi_under = len([r for r in parsed if r["bmi_category"] == "Underweight"])
    bmi_norm = len([r for r in parsed if r["bmi_category"] == "Normal"])
    bmi_over = len([r for r in parsed if r["bmi_category"] == "Overweight"])
    bmi_obese = len([r for r in parsed if r["bmi_category"] == "Obese"])
    bmi_norm_pct = round((bmi_norm / total) * 100, 1)

    vital_risk_radar = [
        {
            "metric": "Blood Pressure",
            "icon": "🩺",
            "normal_pct": optimal_pct,
            "flag_pct": round(100 - optimal_pct, 1),
            "flag_count": total - bp_optimal,
            "average": f"{avg_sys}/{avg_dia} mmHg" if avg_sys else "—",
            "status": "Optimal" if optimal_pct >= 70 else "Needs Monitoring"
        },
        {
            "metric": "Heart Rate",
            "icon": "❤️",
            "normal_pct": hr_normal_pct,
            "flag_pct": round(100 - hr_normal_pct, 1),
            "flag_count": total - hr_normal,
            "average": f"{avg_hr} BPM" if avg_hr else "—",
            "status": "Optimal" if hr_normal_pct >= 75 else "Needs Monitoring"
        },
        {
            "metric": "Oxygen Saturation",
            "icon": "💧",
            "normal_pct": spo2_normal_pct,
            "flag_pct": spo2_risk_pct,
            "flag_count": spo2_low,
            "average": f"{avg_spo2}% SpO2" if avg_spo2 else "—",
            "status": "Optimal" if spo2_normal_pct >= 90 else "Attention Required"
        },
        {
            "metric": "Body Temperature",
            "icon": "🌡️",
            "normal_pct": temp_normal_pct,
            "flag_pct": round(100 - temp_normal_pct, 1),
            "flag_count": total - temp_normal,
            "average": f"{avg_temp}°C" if avg_temp else "—",
            "status": "Optimal" if temp_normal_pct >= 85 else "Fever Watch"
        },
        {
            "metric": "Body Mass Index",
            "icon": "⚖️",
            "normal_pct": bmi_norm_pct,
            "flag_pct": round(100 - bmi_norm_pct, 1),
            "flag_count": total - bmi_norm,
            "average": f"{avg_bmi} kg/m²" if avg_bmi else "—",
            "status": "Healthy" if bmi_norm_pct >= 60 else "Dietary Review"
        }
    ]

    return {
        "total_records": total,
        "normal_count": normal_cnt,
        "attention_count": attention_cnt,
        "compliance_rate": compliance_rate,
        "bp": {
            "avg_sys": avg_sys,
            "avg_dia": avg_dia,
            "bp_str": f"{avg_sys}/{avg_dia}" if avg_sys else "—",
            "min_sys": min_sys,
            "max_sys": max_sys,
            "min_dia": min_dia,
            "max_dia": max_dia,
            "optimal": bp_optimal,
            "optimal_pct": optimal_pct,
            "elevated": bp_elevated,
            "elevated_pct": round((bp_elevated / total) * 100, 1),
            "stage2": bp_stage2,
            "stage2_pct": round((bp_stage2 / total) * 100, 1),
            "low": bp_low,
            "low_pct": round((bp_low / total) * 100, 1),
            "hypertensive_pct": hypertensive_pct
        },
        "hr": {
            "avg": avg_hr,
            "min": min_hr,
            "max": max_hr,
            "normal": hr_normal,
            "normal_pct": hr_normal_pct,
            "tachycardia": hr_tachy,
            "tachycardia_pct": round((hr_tachy / total) * 100, 1),
            "bradycardia": hr_brady,
            "bradycardia_pct": round((hr_brady / total) * 100, 1),
            "flag_pct": round(100 - hr_normal_pct, 1)
        },
        "spo2": {
            "avg": avg_spo2,
            "min": min_spo2,
            "max": max_spo2,
            "normal": spo2_normal,
            "normal_pct": spo2_normal_pct,
            "low": spo2_low,
            "risk_pct": spo2_risk_pct
        },
        "temp": {
            "avg": avg_temp,
            "min": min_temp,
            "max": max_temp,
            "normal": temp_normal,
            "normal_pct": temp_normal_pct,
            "fever": temp_fever,
            "fever_pct": temp_fever_pct,
            "low": temp_low,
            "low_pct": round((temp_low / total) * 100, 1)
        },
        "bmi": {
            "avg_bmi": avg_bmi,
            "avg_weight": avg_weight,
            "avg_height": avg_height,
            "underweight": bmi_under,
            "underweight_pct": round((bmi_under / total) * 100, 1),
            "normal": bmi_norm,
            "normal_pct": bmi_norm_pct,
            "overweight": bmi_over,
            "overweight_pct": round((bmi_over / total) * 100, 1),
            "obese": bmi_obese,
            "obese_pct": round((bmi_obese / total) * 100, 1)
        },
        "vital_risk_radar": vital_risk_radar
    }


def status_trends():
    records_list = get_records()
    labels = ["Normal", "Needs Attention"]
    total = len(records_list) if records_list else 1
    trend_data = []

    for label in labels:
        if label == "Normal":
            count = len([record for record in records_list if record["status"] == "Normal"])
        else:
            count = len([record for record in records_list if record["status"] != "Normal"])
        percentage = round((count / total) * 100)

        trend_data.append({
            "label": label,
            "count": count,
            "percentage": percentage
        })

    return trend_data


def ehr_patient_summaries():
    summaries = []
    patients_list = get_patients()

    for patient in patients_list:
        patient_records = get_records_for_patient(patient["id"])
        latest_record = patient_records[-1] if patient_records else None

        summaries.append({
            "patient": patient,
            "record_count": len(patient_records),
            "latest_record": latest_record
        })

    return summaries


def make_safe_filename(text):
    safe_text = text.lower().strip()
    safe_text = safe_text.replace(" ", "_")

    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789_"

    cleaned = "".join(
        character for character in safe_text
        if character in allowed_characters
    )

    if cleaned:
        return cleaned

    return "patient"


# --------------------------------------------------
# ADMIN AUTHENTICATION HELPERS
# --------------------------------------------------

def username_exists(username, current_admin_id=None):
    admin_users_list = get_admin_users()
    for admin in admin_users_list:
        same_username = admin["username"].lower() == username.lower()
        different_user = current_admin_id is None or admin["id"] != current_admin_id

        if same_username and different_user:
            return True

    return False


def get_current_admin_name():
    return session.get("admin_name", "Clinic Admin")


def get_current_admin_role():
    return session.get("admin_role", "System Admin")


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login_page"))

        return route_function(*args, **kwargs)

    return wrapper


def system_admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login_page"))

        if session.get("admin_role") != "System Admin":
            flash("Only System Admin can access user management.", "error")
            return redirect(url_for("dashboard"))

        return route_function(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# AUTH ROUTES
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "admin_id" in session:
        return redirect(url_for("dashboard"))

    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = get_admin_by_username(username)

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"]
            session["admin_role"] = admin["role"]

            add_access_log(
                user=admin["full_name"],
                role=admin["role"],
                action="Logged in to the E-Wellness system"
            )

            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        error = "Invalid username or password."
        flash("Invalid username or password.", "error")

    return render_template(
        "auth/login.html",
        title="Admin Login",
        error=error
    )


@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    if "admin_id" in session:
        return redirect(url_for("dashboard"))

    error = ""

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not username or not role or not password or not confirm_password:
            error = "Please complete all required fields."
            flash("Please complete all required fields.", "warning")
        elif get_admin_by_username(username):
            error = "Username already exists."
            flash("Username already exists.", "error")
        elif password != confirm_password:
            error = "Passwords do not match."
            flash("Passwords do not match.", "error")
        else:
            new_admin = {
                "id": get_next_admin_id(),
                "full_name": full_name,
                "username": username,
                "role": role,
                "password_hash": generate_password_hash(password)
            }

            add_admin_user(new_admin)

            session["admin_id"] = new_admin["id"]
            session["admin_name"] = new_admin["full_name"]
            session["admin_role"] = new_admin["role"]

            add_access_log(
                user=new_admin["full_name"],
                role=new_admin["role"],
                action="Created an admin account and logged in"
            )

            flash("Admin account created successfully.", "success")
            return redirect(url_for("dashboard"))

    return render_template(
        "auth/signup.html",
        title="Admin Signup",
        error=error
    )


@app.route("/logout")
@login_required
def logout_page():
    admin_name = get_current_admin_name()
    admin_role = get_current_admin_role()

    add_access_log(
        user=admin_name,
        role=admin_role,
        action="Logged out of the E-Wellness system"
    )

    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login_page"))


# --------------------------------------------------
# USER MANAGEMENT ROUTES
# --------------------------------------------------

@app.route("/users")
@system_admin_required
def users_page():
    return render_template(
        "admin/users.html",
        title="User Management",
        active_page="users",
        admin_users=get_admin_users()
    )


@app.route("/users/add", methods=["GET", "POST"])
@system_admin_required
def add_user_page():
    error = ""

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not full_name or not username or not role or not password or not confirm_password:
            error = "Please complete all required fields."
            flash("Please complete all required fields.", "warning")
        elif username_exists(username):
            error = "Username already exists."
            flash("Username already exists.", "error")
        elif password != confirm_password:
            error = "Passwords do not match."
            flash("Passwords do not match.", "error")
        else:
            new_admin = {
                "id": get_next_admin_id(),
                "full_name": full_name,
                "username": username,
                "role": role,
                "password_hash": generate_password_hash(password)
            }

            add_admin_user(new_admin)

            add_access_log(
                user=get_current_admin_name(),
                role=get_current_admin_role(),
                action=f'Created user account for {full_name} as {role}'
            )

            flash("User account added successfully.", "success")
            return redirect(url_for("users_page"))

    return render_template(
        "admin/user_form.html",
        title="Add User",
        active_page="users",
        mode="add",
        user=None,
        error=error
    )


@app.route("/users/edit/<int:admin_id>", methods=["GET", "POST"])
@system_admin_required
def edit_user_page(admin_id):
    admin = get_admin_by_id(admin_id)

    if admin is None:
        flash("User account not found.", "error")
        return redirect(url_for("users_page"))

    error = ""

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not full_name or not username or not role:
            error = "Please complete all required fields."
            flash("Please complete all required fields.", "warning")
        elif username_exists(username, current_admin_id=admin_id):
            error = "Username already exists."
            flash("Username already exists.", "error")
        elif password and password != confirm_password:
            error = "Passwords do not match."
            flash("Passwords do not match.", "error")
        elif session.get("admin_id") == admin_id and role != "System Admin":
            error = "You cannot change your own System Admin role."
            flash("You cannot change your own System Admin role.", "warning")
        else:
            old_name = admin["full_name"]
            old_role = admin["role"]

            update_data = {
                "full_name": full_name,
                "username": username,
                "role": role
            }

            if password:
                update_data["password_hash"] = generate_password_hash(password)

            update_admin_user(admin_id, update_data)

            if session.get("admin_id") == admin_id:
                session["admin_name"] = full_name
                session["admin_role"] = role

            add_access_log(
                user=get_current_admin_name(),
                role=get_current_admin_role(),
                action=f'Updated user account {old_name} from {old_role} to {role}'
            )

            flash("User account updated successfully.", "success")
            return redirect(url_for("users_page"))

    return render_template(
        "admin/user_form.html",
        title="Edit User",
        active_page="users",
        mode="edit",
        user=admin,
        error=error
    )


@app.route("/users/delete/<int:admin_id>", methods=["POST"])
@system_admin_required
def delete_user_page(admin_id):
    admin = get_admin_by_id(admin_id)

    if admin is None:
        flash("User account not found.", "error")
        return redirect(url_for("users_page"))

    if session.get("admin_id") == admin_id:
        flash("You cannot delete your own logged-in account.", "warning")
        return redirect(url_for("users_page"))

    admin_users_list = get_admin_users()
    system_admin_count = len([
        user for user in admin_users_list
        if user["role"] == "System Admin"
    ])

    if admin["role"] == "System Admin" and system_admin_count <= 1:
        flash("At least one System Admin account must remain.", "warning")
        return redirect(url_for("users_page"))

    deleted_name = admin["full_name"]
    deleted_role = admin["role"]

    delete_admin_user(admin_id)

    add_access_log(
        user=get_current_admin_name(),
        role=get_current_admin_role(),
        action=f'Deleted user account for {deleted_name} with role {deleted_role}'
    )

    flash("User account deleted successfully.", "success")
    return redirect(url_for("users_page"))



# --------------------------------------------------
# PAGE ROUTES
# --------------------------------------------------

@app.route("/")
@login_required
def dashboard():
    records_list = get_records()
    patients_list = get_patients()

    # Get all records in reverse order (newest first)
    latest_records = list(reversed(records_list))

    return render_template(
        "admin/dashboard.html",
        title="Dashboard",
        active_page="dashboard",
        stats=dashboard_stats(),
        latest_records=latest_records,
        bmi_trends=bmi_trends(),
        status_trends=status_trends(),
        bmi_chart_records=bmi_chart_records(),
        vitals_chart_records=all_vitals_chart_records(records_list),
        analytics=comprehensive_vitals_analytics(records_list),
        patients=patients_list
    )


@app.route("/patients")
@login_required
def patients_page():
    search = request.args.get("search", "").lower().strip()
    patients_list = get_patients()

    # Ensure age is populated for each patient
    for patient in patients_list:
        if not patient.get("age"):
            calc_age = calculate_age(patient.get("birth_date", ""))
            patient["age"] = calc_age if calc_age > 0 else 0

    if search:
        filtered_patients = [
            patient for patient in patients_list
            if search in f'{patient["first_name"]} {patient["last_name"]}'.lower()
            or search in patient["barangay"].lower()
            or search in patient["gender"].lower()
            or search in patient["contact_no"].lower()
        ]
    else:
        filtered_patients = patients_list

    return render_template(
        "admin/patients.html",
        title="Patient Management",
        active_page="patients",
        patients=filtered_patients,
        search=search
    )


@app.route("/add-patient", methods=["GET", "POST"])
@login_required
def add_patient_page():
    if request.method == "POST":
        age = int(request.form.get("age", 0))

        new_patient = {
            "id": get_next_patient_id(),
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "contact_no": request.form.get("contact_no", "").strip(),
            "barangay": request.form.get("barangay", "").strip()
        }

        created_patient_id = add_patient(new_patient)
        if created_patient_id:
            new_patient["id"] = created_patient_id

        # Parse blood pressure (format: "120/80")
        blood_pressure = request.form.get("blood_pressure", "").strip()
        try:
            bp_parts = blood_pressure.split("/")
            systolic = int(bp_parts[0]) if len(bp_parts) > 0 else 0
            diastolic = int(bp_parts[1]) if len(bp_parts) > 1 else 0
        except:
            systolic = 0
            diastolic = 0

        body_temp = float(request.form.get("body_temp", 36.5))
        heart_rate = int(request.form.get("heart_rate", 75))
        oxygen_saturation = int(request.form.get("oxygen_saturation", 98))
        height = float(request.form.get("height", 160))
        weight = float(request.form.get("weight", 55))
        bmi_input = request.form.get("bmi", "").strip()

        # Calculate BMI if not provided
        if bmi_input:
            bmi = float(bmi_input)
        else:
            bmi = calculate_bmi(height, weight)

        new_record = create_health_record(
            patient_id=new_patient["id"],
            temperature=body_temp,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            systolic=systolic,
            diastolic=diastolic,
            height=height,
            weight=weight,
            age=age
        )

        add_access_log(
            user=get_current_admin_name(),
            role=get_current_admin_role(),
            action=f'Added patient manually with initial health record for {new_patient["first_name"]} {new_patient["last_name"]}'
        )

        flash("Patient registered and health assessment recorded. Reviewing Current Well Being Assessment.", "success")
        return redirect(url_for("wellbeing_assessment_page", patient_id=new_patient["id"], record_id=new_record.get("id")))

    return render_template(
        "admin/add_patient.html",
        title="Add Patient Manually",
        active_page="patients"
    )


@app.route("/ehr-records")
@login_required
def ehr_records_page():
    return render_template(
        "admin/ehr_records.html",
        title="Electronic Health Records",
        active_page="ehr_records",
        patient_summaries=ehr_patient_summaries()
    )


@app.route("/ehr-records/patient/<int:patient_id>")
@login_required
def patient_record_history_page(patient_id):
    patient = get_patient_by_id(patient_id)

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("ehr_records_page"))

    patient_records_raw = get_records_for_patient(patient_id)
    patient_records = list(reversed(patient_records_raw))
    latest_record = patient_records[0] if patient_records else None

    patient_chart_records = all_vitals_chart_records(patient_records_raw)
    patient_analytics = comprehensive_vitals_analytics(patient_records_raw)

    add_access_log(
        user=get_current_admin_name(),
        role=get_current_admin_role(),
        action=f'Viewed health record history for {patient["first_name"]} {patient["last_name"]}'
    )

    return render_template(
        "admin/patient_record_history.html",
        title="Patient Health Records",
        active_page="ehr_records",
        patient=patient,
        records=patient_records,
        latest_record=latest_record,
        patient_chart_records=patient_chart_records,
        patient_analytics=patient_analytics
    )


@app.route("/download-patient-history/<int:patient_id>")
@login_required
def download_patient_history(patient_id):
    patient = get_patient_by_id(patient_id)

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("ehr_records_page"))

    patient_records = list(reversed(get_records_for_patient(patient_id)))

    first_name = patient.get("first_name", "")
    last_name = patient.get("last_name", "")
    patient_name = f"{first_name} {last_name}".strip() or f"Patient_{patient_id}"
    generated_at = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    story.append(Paragraph("E-Wellness Patient Health History", title_style))
    story.append(Spacer(1, 10))

    patient_info = f"""
    <b>Patient Name:</b> {patient_name}<br/>
    <b>Gender:</b> {patient.get("gender", "Not specified")}<br/>
    <b>Age:</b> {patient.get("age") or "N/A"}<br/>
    <b>Contact Number:</b> {patient.get("contact_no") or "N/A"}<br/>
    <b>Barangay:</b> {patient.get("barangay") or "N/A"}<br/>
    <b>Generated At:</b> {generated_at}
    """

    story.append(Paragraph(patient_info, normal_style))
    story.append(Spacer(1, 14))

    total_records = len(patient_records)
    latest_record = patient_records[0] if patient_records else None

    if latest_record:
        latest_bmi = latest_record.get("M") or latest_record.get("bmi") or "—"
        latest_bmi_cat = latest_record.get("bmi_category") or "—"
        latest_status = latest_record.get("status") or "Normal"
        latest_date = latest_record.get("created_at") or f"{latest_record.get('A', '')} {latest_record.get('B', '')}".strip() or "—"

        if latest_status == "Normal" or (latest_status == "Needs Attention" and latest_bmi_cat == "Normal"):
            display_status = "Normal"
        else:
            display_status = latest_status

        summary_info = f"""
        <b>Total Records:</b> {total_records}<br/>
        <b>Latest BMI:</b> {latest_bmi} ({latest_bmi_cat})<br/>
        <b>Latest Status:</b> {display_status}<br/>
        <b>Latest Record Date:</b> {latest_date}
        """
    else:
        summary_info = """
        <b>Total Records:</b> 0<br/>
        <b>Latest BMI:</b> No record yet<br/>
        <b>Latest Status:</b> No record yet<br/>
        <b>Latest Record Date:</b> No record yet
        """

    story.append(Paragraph("Patient Summary", heading_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(summary_info, normal_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Health Record History", heading_style))
    story.append(Spacer(1, 8))

    if patient_records:
        table_data = [
            [
                "Date",
                "Vitals",
                "BMI",
                "Status",
                "Remarks"
            ]
        ]

        for record in patient_records:
            temp = record.get("J") or record.get("temperature") or record.get("body_temp") or "—"
            hr = record.get("H") or record.get("heart_rate") or "—"
            spo2 = record.get("I") or record.get("oxygen_saturation") or "—"
            bp = record.get("G") or record.get("blood_pressure") or "—"
            height = record.get("L") or record.get("height") or "—"
            weight = record.get("K") or record.get("weight") or "—"
            bmi_val = record.get("M") or record.get("bmi") or "—"
            bmi_cat = record.get("bmi_category") or "—"
            rec_status = record.get("status") or "Normal"
            remarks = record.get("remarks") or "None"
            rec_date = record.get("created_at") or f"{record.get('A', '')} {record.get('B', '')}".strip() or "—"

            vitals = (
                f"Temp: {temp} °C<br/>"
                f"HR: {hr} bpm<br/>"
                f"SpO2: {spo2}%<br/>"
                f"BP: {bp}<br/>"
                f"Height: {height} cm<br/>"
                f"Weight: {weight} kg"
            )

            bmi_display = f"{bmi_val}<br/>{bmi_cat}"

            if rec_status == "Normal" or (rec_status == "Needs Attention" and bmi_cat == "Normal"):
                display_rec_status = "Normal"
            else:
                display_rec_status = rec_status

            table_data.append([
                Paragraph(str(rec_date), normal_style),
                Paragraph(vitals, normal_style),
                Paragraph(bmi_display, normal_style),
                Paragraph(display_rec_status, normal_style),
                Paragraph(str(remarks), normal_style)
            ])

        table = Table(
            table_data,
            colWidths=[
                1.3 * inch,
                1.6 * inch,
                0.9 * inch,
                1.1 * inch,
                2.3 * inch
            ],
            repeatRows=1
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f6bff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce8f7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff"))
        ]))

        story.append(table)
    else:
        story.append(Paragraph("No health records available for this patient.", normal_style))

    story.append(Spacer(1, 18))

    footer_text = (
        "Generated by E-Wellness Health Monitoring EHR System. "
        "This document is intended for healthcare monitoring and patient record review."
    )

    story.append(Paragraph(footer_text, normal_style))

    pdf.build(story)
    buffer.seek(0)

    add_access_log(
        user=get_current_admin_name(),
        role=get_current_admin_role(),
        action=f"Downloaded health history PDF for {patient_name}"
    )

    filename = f"{make_safe_filename(patient_name)}_health_history.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


@app.route("/patients/<int:patient_id>/wellbeing-assessment", methods=["GET", "POST"])
@app.route("/patients/<int:patient_id>/wellbeing-assessment/<int:record_id>", methods=["GET", "POST"])
@login_required
def wellbeing_assessment_page(patient_id, record_id=None):
    patient = get_patient_by_id(patient_id)
    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for("patients_page"))

    patient_records = get_records_for_patient(patient_id)
    if not patient_records:
        flash("No health assessment records found for this patient.", "warning")
        return redirect(url_for("patient_record_history_page", patient_id=patient_id))

    selected_record = None
    if record_id:
        for r in patient_records:
            if r.get("id") == record_id:
                selected_record = r
                break

    if not selected_record:
        selected_record = patient_records[-1]

    if request.method == "POST":
        survey_data = {
            "sleep": request.form.get("sleep", "7_to_8"),
            "activity": request.form.get("activity", "moderate"),
            "stress": request.form.get("stress", "low"),
            "hydration_diet": request.form.get("hydration_diet", "good"),
            "symptoms": request.form.get("symptoms", "none")
        }
        save_wellbeing_survey(patient_id, selected_record.get("id"), survey_data)
        add_access_log(
            user=get_current_admin_name(),
            role=get_current_admin_role(),
            action=f'Completed 5-question Well-Being Survey for {patient.get("first_name")} {patient.get("last_name")}'
        )
        flash("Well-Being Survey saved! Assessment guidance has been personalized for this patient.", "success")
        return redirect(url_for("wellbeing_assessment_page", patient_id=patient_id, record_id=selected_record.get("id")))

    if selected_record and selected_record.get("E"):
        try:
            patient["age"] = int(selected_record["E"])
        except:
            pass
    if not patient.get("age"):
        calc_age = calculate_age(patient.get("birth_date", ""))
        patient["age"] = calc_age if calc_age > 0 else 0

    survey = get_wellbeing_survey(patient_id, selected_record.get("id"), selected_record)
    assessment = get_wellbeing_assessment(selected_record, patient, survey=survey)

    add_access_log(
        user=get_current_admin_name(),
        role=get_current_admin_role(),
        action=f'Viewed Current Well Being Assessment for {patient.get("first_name")} {patient.get("last_name")}'
    )

    return render_template(
        "admin/wellbeing_assessment.html",
        title="Current Well Being Assessment",
        active_page="patients",
        patient=patient,
        record=selected_record,
        assessment=assessment,
        all_records=list(reversed(patient_records))
    )


@app.route("/add-health-record", methods=["GET", "POST"])
@login_required
def add_health_record_page():
    selected_patient_id = request.args.get("patient_id", type=int)

    if request.method == "POST":
        patient_id = int(request.form.get("patient_id"))

        temperature = float(request.form.get("temperature", 36.5))
        heart_rate = int(request.form.get("heart_rate", 75))
        oxygen_saturation = int(request.form.get("oxygen_saturation", 98))
        systolic = int(request.form.get("systolic", 120))
        diastolic = int(request.form.get("diastolic", 80))
        height = float(request.form.get("height", 160))
        weight = float(request.form.get("weight", 55))

        new_record = create_health_record(
            patient_id=patient_id,
            temperature=temperature,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            systolic=systolic,
            diastolic=diastolic,
            height=height,
            weight=weight
        )

        add_access_log(
            user=get_current_admin_name(),
            role=get_current_admin_role(),
            action=f'Added follow-up health record for {new_record["C"]} {new_record["D"]}'
        )

        flash("Health record added successfully. Reviewing Current Well Being Assessment.", "success")
        return redirect(url_for("wellbeing_assessment_page", patient_id=patient_id, record_id=new_record.get("id")))

    if not selected_patient_id:
        flash("Please select a patient before adding a health record.", "warning")
        return redirect(url_for("patients_page"))

    selected_patient = get_patient_by_id(selected_patient_id)

    if not selected_patient:
        flash("Patient record not found.", "error")
        return redirect(url_for("patients_page"))

    return render_template(
        "admin/add_health_record.html",
        title="Add Health Record",
        active_page="ehr_records",
        selected_patient=selected_patient
    )


@app.route("/reports")
@login_required
def reports_page():
    records_list = get_records()
    patients_list = get_patients()
    return render_template(
        "admin/reports.html",
        title="Reports and Analytics",
        active_page="reports",
        stats=dashboard_stats(),
        bmi_trends=bmi_trends(),
        status_trends=status_trends(),
        bmi_chart_records=bmi_chart_records(),
        vitals_chart_records=all_vitals_chart_records(records_list),
        analytics=comprehensive_vitals_analytics(records_list),
        patients=patients_list,
        records=list(reversed(records_list))
    )


@app.route("/security")
@login_required
def security_page():
    return render_template(
        "admin/security.html",
        title="Security and Audit Logs",
        active_page="security",
        logs=get_access_logs()
    )


# --------------------------------------------------
# DATA IMPORT ROUTES
# --------------------------------------------------

@app.route("/import")
@login_required
def import_data_page():
    return render_template(
        "admin/import_data.html",
        title="Import Data",
        active_page="import"
    )


@app.route("/import/kiosk", methods=["POST"])
@login_required
def import_kiosk_data():
    if "file" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("import_data_page"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("import_data_page"))

    try:
        if file.filename.endswith(".csv"):
            imported_count = import_kiosk_csv(file)
            flash(f"Successfully imported {imported_count} health records.", "success")
        elif file.filename.endswith(".json"):
            imported_count = import_kiosk_json(file)
            flash(f"Successfully imported {imported_count} health records.", "success")
        else:
            flash("Invalid file format. Please upload CSV or JSON.", "error")
            return redirect(url_for("import_data_page"))

        add_access_log(
            user=get_current_admin_name(),
            role=get_current_admin_role(),
            action=f"Imported {imported_count} health records from {file.filename}"
        )

    except Exception as e:
        flash(f"Error importing health records: {str(e)}", "error")
        return redirect(url_for("import_data_page"))

    return redirect(url_for("import_data_page"))


@app.route("/import/patients", methods=["POST"])
@login_required
def import_patients():
    if "file" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("import_data_page"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("import_data_page"))

    try:
        if file.filename.endswith(".csv"):
            imported_count = import_patients_from_csv(file)
            flash(f"Successfully imported {imported_count} patients from CSV.", "success")
        elif file.filename.endswith(".json"):
            imported_count = import_patients_from_json(file)
            flash(f"Successfully imported {imported_count} patients from JSON.", "success")
        else:
            flash("Invalid file format. Please upload CSV or JSON.", "error")
            return redirect(url_for("import_data_page"))

        add_access_log(
            user=get_current_admin_name(),
            role=get_current_admin_role(),
            action=f"Imported {imported_count} patients from {file.filename}"
        )

    except Exception as e:
        flash(f"Error importing patients: {str(e)}", "error")
        return redirect(url_for("import_data_page"))

    return redirect(url_for("import_data_page"))


@app.route("/import/records", methods=["POST"])
@login_required
def import_records():
    if "file" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("import_data_page"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("import_data_page"))

    try:
        if file.filename.endswith(".csv"):
            imported_count = import_records_from_csv(file)
            flash(f"Successfully imported {imported_count} health records from CSV.", "success")
        elif file.filename.endswith(".json"):
            imported_count = import_records_from_json(file)
            flash(f"Successfully imported {imported_count} health records from JSON.", "success")
        else:
            flash("Invalid file format. Please upload CSV or JSON.", "error")
            return redirect(url_for("import_data_page"))

        add_access_log(
            user=get_current_admin_name(),
            role=get_current_admin_role(),
            action=f"Imported {imported_count} health records from {file.filename}"
        )

    except Exception as e:
        flash(f"Error importing health records: {str(e)}", "error")
        return redirect(url_for("import_data_page"))

    return redirect(url_for("import_data_page"))


def import_patients_from_csv(file):
    imported_count = 0
    patients_list = get_patients()
    existing_ids = {p["id"] for p in patients_list}
    max_id = max(existing_ids) if existing_ids else 0

    csv_reader = csv.DictReader(file.read().decode("utf-8").splitlines())
    for row in csv_reader:
        max_id += 1
        new_patient = {
            "id": max_id,
            "first_name": row.get("first_name", "").strip(),
            "last_name": row.get("last_name", "").strip(),
            "gender": row.get("gender", "Not specified").strip(),
            "contact_no": row.get("contact_no", "").strip(),
            "barangay": row.get("barangay", "").strip()
        }
        add_patient(new_patient)
        imported_count += 1

    return imported_count


def import_patients_from_json(file):
    imported_count = 0
    data = json.load(file)
    patients_list = get_patients()
    existing_ids = {p["id"] for p in patients_list}
    max_id = max(existing_ids) if existing_ids else 0

    for patient_data in data:
        max_id += 1
        new_patient = {
            "id": max_id,
            "first_name": patient_data.get("first_name", "").strip(),
            "last_name": patient_data.get("last_name", "").strip(),
            "gender": patient_data.get("gender", "Not specified").strip(),
            "contact_no": patient_data.get("contact_no", "").strip(),
            "barangay": patient_data.get("barangay", "").strip()
        }
        add_patient(new_patient)
        imported_count += 1

    return imported_count


def import_records_from_csv(file):
    imported_count = 0
    records_list = get_records()
    existing_ids = {r["id"] for r in records_list}
    max_id = max(existing_ids) if existing_ids else 0

    csv_reader = csv.DictReader(file.read().decode("utf-8").splitlines())
    for row in csv_reader:
        max_id += 1
        patient_id = int(row.get("patient_id", 0))
        patient = get_patient_by_id(patient_id)

        if not patient:
            continue

        temperature = float(row.get("temperature", 0))
        heart_rate = int(row.get("heart_rate", 0))
        oxygen_saturation = int(row.get("oxygen_saturation", 0))
        systolic = int(row.get("systolic", 0))
        diastolic = int(row.get("diastolic", 0))
        height = float(row.get("height", 0))
        weight = float(row.get("weight", 0))

        new_record = create_health_record(
            patient_id=patient_id,
            temperature=temperature,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            systolic=systolic,
            diastolic=diastolic,
            height=height,
            weight=weight
        )
        imported_count += 1

    return imported_count


def import_records_from_json(file):
    imported_count = 0
    data = json.load(file)
    records_list = get_records()
    existing_ids = {r["id"] for r in records_list}
    max_id = max(existing_ids) if existing_ids else 0

    for record_data in data:
        max_id += 1
        patient_id = int(record_data.get("patient_id", 0))
        patient = get_patient_by_id(patient_id)

        if not patient:
            continue

        temperature = float(record_data.get("temperature", 0))
        heart_rate = int(record_data.get("heart_rate", 0))
        oxygen_saturation = int(record_data.get("oxygen_saturation", 0))
        systolic = int(record_data.get("systolic", 0))
        diastolic = int(record_data.get("diastolic", 0))
        height = float(record_data.get("height", 0))
        weight = float(record_data.get("weight", 0))

        new_record = create_health_record(
            patient_id=patient_id,
            temperature=temperature,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            systolic=systolic,
            diastolic=diastolic,
            height=height,
            weight=weight
        )
        imported_count += 1

    return imported_count


def import_kiosk_csv(file):
    imported_count = 0
    csv_reader = csv.DictReader(file.read().decode("utf-8").splitlines())

    patients_list = get_patients()
    existing_patient_ids = {p["id"] for p in patients_list}
    max_patient_id = max(existing_patient_ids) if existing_patient_ids else 0

    for record in csv_reader:
        # Parse kiosk format with letter keys or verbose names
        first_name = record.get("FirstName", record.get("C", "")).strip()
        last_name = record.get("LastName", record.get("D", "")).strip()
        age_str = record.get("Age", record.get("E", "0"))
        gender = record.get("Gender", record.get("F", "")).strip()
        blood_pressure = record.get("BloodPressure", record.get("G", "")).strip()
        heart_rate_str = record.get("HeartRate_BPM", record.get("HeartRate", record.get("H", "0")))
        oxygen_saturation_str = record.get("OxygenSaturation_pct", record.get("OxygenSaturation", record.get("I", "0")))
        body_temp_str = record.get("BodyTemp_C", record.get("BodyTemp", record.get("J", "0")))
        weight_str = record.get("Weight_kg", record.get("Weight", record.get("K", "0")))
        height_str = record.get("Height_cm", record.get("Height", record.get("L", "0")))
        bmi_str = record.get("BMI", record.get("M", "0"))

        # Skip header rows (if values are field names)
        if age_str == "Age" or first_name == "FirstName":
            continue

        try: age = int(age_str)
        except: age = 0
        try: heart_rate = int(heart_rate_str)
        except: heart_rate = 0
        try: oxygen_saturation = int(oxygen_saturation_str)
        except: oxygen_saturation = 0
        try: body_temp = float(body_temp_str)
        except: body_temp = 0.0
        try: weight = float(weight_str)
        except: weight = 0.0
        try: height = float(height_str)
        except: height = 0.0
        try: bmi = float(bmi_str)
        except: bmi = 0.0

        existing_patient = None
        for patient in patients_list:
            if patient["first_name"] == first_name and patient["last_name"] == last_name:
                existing_patient = patient
                break

        if not existing_patient:
            max_patient_id += 1
            new_patient = {
                "id": max_patient_id,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "contact_no": "",
                "barangay": ""
            }
            add_patient(new_patient)
            new_patient["age"] = age
            patients_list.append(new_patient)
            patient_id = max_patient_id
        else:
            patient_id = existing_patient["id"]

        try:
            bp_parts = blood_pressure.split("/")
            systolic = int(bp_parts[0]) if len(bp_parts) > 0 else 0
            diastolic = int(bp_parts[1]) if len(bp_parts) > 1 else 0
        except:
            systolic = 0
            diastolic = 0

        create_health_record(
            patient_id=patient_id,
            temperature=body_temp,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            systolic=systolic,
            diastolic=diastolic,
            height=height,
            weight=weight,
            age=age
        )
        imported_count += 1

    return imported_count


def import_kiosk_json(file):
    imported_count = 0
    data = json.load(file)

    # Handle both single record and array of records
    if isinstance(data, dict):
        data = [data]

    patients_list = get_patients()
    records_list = get_records()
    existing_patient_ids = {p["id"] for p in patients_list}
    max_patient_id = max(existing_patient_ids) if existing_patient_ids else 0
    existing_record_ids = {r["id"] for r in records_list}
    max_record_id = max(existing_record_ids) if existing_record_ids else 0

    for record in data:
        # Parse kiosk format with letter keys
        first_name = record.get("C", "").strip()
        last_name = record.get("D", "").strip()
        age_str = record.get("E", "0")
        gender = record.get("F", "").strip()
        blood_pressure = record.get("G", "").strip()
        heart_rate_str = record.get("H", "0")
        oxygen_saturation_str = record.get("I", "0")
        body_temp_str = record.get("J", "0")
        weight_str = record.get("K", "0")
        height_str = record.get("L", "0")
        bmi_str = record.get("M", "0")

        # Skip header rows (if values are field names)
        if age_str == "Age" or first_name == "FirstName":
            continue

        # Convert to appropriate types with error handling
        try:
            age = int(age_str)
        except:
            age = 0

        try:
            heart_rate = int(heart_rate_str)
        except:
            heart_rate = 0

        try:
            oxygen_saturation = int(oxygen_saturation_str)
        except:
            oxygen_saturation = 0

        try:
            body_temp = float(body_temp_str)
        except:
            body_temp = 0.0

        try:
            weight = float(weight_str)
        except:
            weight = 0.0

        try:
            height = float(height_str)
        except:
            height = 0.0

        try:
            bmi = float(bmi_str)
        except:
            bmi = 0.0

        # Check if patient already exists (by name)
        existing_patient = None
        for patient in patients_list:
            if patient["first_name"] == first_name and patient["last_name"] == last_name:
                existing_patient = patient
                break

        if not existing_patient:
            # Create new patient
            max_patient_id += 1
            new_patient = {
                "id": max_patient_id,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "contact_no": "",
                "barangay": ""
            }
            add_patient(new_patient)
            new_patient["age"] = age
            patients_list.append(new_patient)
            patient_id = max_patient_id
        else:
            patient_id = existing_patient["id"]

        # Parse blood pressure (format: "120/80")
        try:
            bp_parts = blood_pressure.split("/")
            systolic = int(bp_parts[0]) if len(bp_parts) > 0 else 0
            diastolic = int(bp_parts[1]) if len(bp_parts) > 1 else 0
        except:
            systolic = 0
            diastolic = 0

        # Create health record
        max_record_id += 1
        new_record = create_health_record(
            patient_id=patient_id,
            temperature=body_temp,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            systolic=systolic,
            diastolic=diastolic,
            height=height,
            weight=weight,
            age=age
        )
        imported_count += 1

    return imported_count


# --------------------------------------------------
# SAMPLE API ROUTES FOR BACKEND PROGRAMMER
# --------------------------------------------------

@app.route("/api/dashboard-data")
@login_required
def api_dashboard_data():
    records_list = get_records()
    return jsonify({
        "stats": dashboard_stats(),
        "bmi_trends": bmi_trends(),
        "status_trends": status_trends(),
        "bmi_chart_records": bmi_chart_records(),
        "vitals_chart_records": all_vitals_chart_records(records_list),
        "analytics": comprehensive_vitals_analytics(records_list)
    })


@app.route("/api/analytics-data")
@login_required
def api_analytics_data():
    records_list = get_records()
    return jsonify({
        "analytics": comprehensive_vitals_analytics(records_list),
        "records": all_vitals_chart_records(records_list)
    })


@app.route("/health")
def health():
    db_status = "disconnected"
    if supabase:
        try:
            # Lightweight query to keep Supabase active and verify connectivity
            supabase.table("patients").select("id").limit(1).execute()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "service": "ewellness",
        "database": db_status
    }), 200


@app.route("/api/records")
@login_required
def api_records():
    return jsonify(get_records())


@app.route("/api/patients")
@login_required
def api_patients():
    return jsonify(get_patients())


if __name__ == "__main__":
    app.run(debug=True)