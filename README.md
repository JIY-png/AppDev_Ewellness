# E-Wellness: Health Monitoring & Electronic Health Record (EHR) System

![E-Wellness Banner](static/E-Wellness%20logo.png)

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat&logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Engine-DA291C?style=flat)](https://www.reportlab.com/)
[![Status](https://img.shields.io/badge/Project-Capstone-blueviolet?style=flat)](#)

---

## 📌 Overview

**E-Wellness** is a dual-interface Health Monitoring and Electronic Health Record (EHR) web application developed as a Capstone project. The system bridges primary community healthcare and administrative clinic management by combining:

1. **Self-Service Patient Health Kiosk (`/kiosk`)**: A patient-friendly, step-by-step guided vital signs check-in station that records body temperature, blood pressure, pulse, height, weight, automated BMI calculation, and oxygen saturation (SpO2).
2. **Clinical EHR & Admin Portal (`/`)**: A secure administrative system for healthcare workers to manage patient databases, monitor population health analytics, review longitudinal health histories, import offline kiosk SD card data, generate downloadable clinical PDF health reports, and audit system activities.

---

## 🚀 Key Features

### 🩺 1. Self-Service Health Kiosk Workflow
- **Patient Check-in**: Streamlined demographic entry (Name, Birthdate, Contact Number, Barangay).
- **Interactive Measurement Stations**:
  - **Body Temperature**: Quick assessment with fever threshold alerts.
  - **Blood Pressure & Heart Rate**: Systolic/diastolic entry, pulse rate tracking, and classification (Normal, Low, High BP).
  - **Height & Weight**: Measurements recorded in centimeters and kilograms.
  - **Automated BMI Calculation**: Immediate BMI index computation and classification (*Underweight*, *Normal*, *Overweight*, *Obese*).
  - **Pulse Oximetry (SpO2)**: Oxygen saturation level capture with hypoxemia warnings (<95%).
- **Automated Health Evaluation**: Evaluates patient vitals against clinical thresholds to flag records as **Normal** or **Needs Attention**.
- **Assessment Review & Submission**: Patients review summary cards before committing data to the central database.

### 📊 2. Clinical EHR & Admin Dashboard
- **Executive Health Metrics**: Real-time counters for total registered patients, total records logged, normal vs. attention-needed cases, average community BMI, and estimated documentation reduction.
- **Visual Analytics**: Interactive BMI and health status trend distribution charts.
- **Patient Management (`/patients`)**: Search, filter, and inspect patients by name, barangay, gender, or contact details; add patients manually with initial vitals.
- **Longitudinal EHR Records (`/ehr-records`)**: Complete timeline of health assessments per patient with historical comparisons.
- **Clinical PDF Report Generation**: On-demand downloadable PDF reports powered by ReportLab containing patient vitals, BMI evaluations, clinical remarks, and timestamped audit information.
- **Offline Data Import (`/import`)**:
  - Direct upload and parsing of kiosk SD card data in **CSV** or **JSON** format.
  - Supports both descriptive headers (`Date`, `FirstName`, `BloodPressure`, etc.) and single-letter kiosk hardware codes (`A` through `M`).
- **Role-Based Access Control (RBAC)**: Distinct permissions for **System Admin** and clinic staff.
- **Audit & Security Logging (`/security`)**: Immutable trail recording logins, account actions, data imports, and report downloads.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Backend Framework** | [Flask](https://flask.palletsprojects.com/) (v3.0+) | Lightweight Python WSGI web application framework |
| **Database** | [Supabase](https://supabase.com/) | Managed cloud PostgreSQL with Row Level Security (RLS) |
| **Database Client** | `supabase-py` (v2.7.0) / `httpx` | Asynchronous & synchronous REST client for Supabase |
| **PDF Generation** | [ReportLab](https://www.reportlab.com/) | Dynamic PDF generation for patient history reports |
| **Frontend** | HTML5, Vanilla CSS3, JavaScript (ES6) | Responsive, mobile-first custom UI with glassmorphism & cards |
| **Authentication & Security** | Werkzeug Security | Password hashing with `scrypt` / `pbkdf2`, session management |
| **Environment Configuration** | `python-dotenv` | Twelve-factor configuration via `.env` file |

---

## 📁 Project Structure

```text
EWELLNESS.UI/
├── app.py                      # Core Flask application and routing logic
├── requirements.txt            # Python dependencies
├── supabase_schema.sql         # SQL schema definitions, indexes, and RLS policies
├── SUPABASE_SETUP.md           # Step-by-step Supabase configuration guide
├── knowledge.md                # Project architecture & knowledge base
├── E-Wellness logo.png         # Project branding asset
├── static/                     # Static web assets
│   ├── style.css               # Comprehensive UI design system & stylesheet
│   ├── script.js               # Frontend interactive scripts, chart rendering, modals
│   └── E-Wellness logo.png     # Logo served statically
├── templates/                  # Jinja2 template hierarchy
│   ├── layouts/
│   │   ├── base.html           # Main administrative layout with sidebar & toasts
│   │   └── kiosk_base.html     # Fullscreen patient kiosk layout
│   ├── auth/
│   │   ├── login.html          # Admin authentication page
│   │   └── signup.html         # User registration page
│   ├── admin/
│   │   ├── dashboard.html      # Main EHR analytics dashboard
│   │   ├── patients.html       # Patient directory & search
│   │   ├── add_patient.html    # Manual patient intake form
│   │   ├── ehr_records.html    # Longitudinal health record lists
│   │   ├── patient_record_history.html # Detailed single-patient record history
│   │   ├── add_health_record.html      # Follow-up health record entry
│   │   ├── reports.html        # Comprehensive clinical report summaries
│   │   ├── import_data.html    # SD card CSV/JSON batch data import
│   │   ├── security.html       # System access & audit logs
│   │   ├── users.html          # User account management (System Admin)
│   │   └── user_form.html      # Add/edit staff user credentials
│   └── kiosk/
│       ├── kiosk_welcome.html  # Kiosk welcome landing screen
│       ├── kiosk_checkin.html  # Patient demographic check-in form
│       ├── kiosk_assessment.html # Station checklist overview
│       ├── kiosk_temperature.html # Body temperature station
│       ├── kiosk_blood_pressure.html # BP & pulse station
│       ├── kiosk_height.html   # Height measurement station
│       ├── kiosk_weight.html   # Weight measurement station
│       ├── kiosk_bmi.html      # Automated BMI calculation station
│       ├── kiosk_spo2.html     # Pulse oximetry station
│       ├── kiosk_summary.html  # Pre-submission review screen
│       └── kiosk_complete.html # Assessment completed confirmation screen
└── .agents/                    # Agent guidance & workflow skills
    └── skills/
        ├── run-dev/            # Instructions for starting the development server
        └── generate-pdf/       # ReportLab PDF styling and boilerplate standards
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.8+** installed on your system.
- A **Supabase** account (Free tier available at [supabase.com](https://supabase.com)).
- Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/JIY-png/EWELLENESS.UI.git
cd EWELLNESS.UI
```

### 3. Create & Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup (Supabase)

1. Log in to [Supabase Dashboard](https://supabase.com/dashboard) and create a new project (e.g., `ewellness-ehr-system`).
2. Navigate to the **SQL Editor** on the left menu.
3. Open [`supabase_schema.sql`](supabase_schema.sql), copy its entire contents, paste them into the SQL editor, and click **Run**.
   - This creates tables: `patients`, `records`, `admin_users`, and `access_logs`.
   - It also establishes indexes, Row Level Security (RLS) rules, and a default administrator user.
4. Go to **Project Settings** > **API**.
5. Copy your **Project URL** and the **`service_role` secret key** (needed for backend database operations).

### Environment Configuration (`.env`)
Create a `.env` file in the project root directory:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-service-role-key-here
```

> ⚠️ **Important**: Use the `service_role` key rather than the public `anon` key so the server can query and update tables with appropriate access permissions.

---

## 🏃 Running the Application

Once your `.env` file is configured and dependencies are installed:

```bash
python app.py
```

By default, the application runs locally at:
```text
http://127.0.0.1:5000/
```

### Default System Administrator Credentials
If seeded using `supabase_schema.sql`:
- **Username:** `admin`
- **Password:** `admin123`

---

## 💻 Usage Guide

### Accessing the Kiosk
Patients can access the dedicated self-assessment station by visiting:
```text
http://127.0.0.1:5000/kiosk
```
1. Click **Start Health Assessment**.
2. Input basic demographic details.
3. Step through vital monitoring stations (Temperature, Blood Pressure, Height, Weight, BMI, and SpO2).
4. Review summary status and submit results to the EHR.

### Accessing the Admin Portal
Healthcare staff and clinic administrators navigate to:
```text
http://127.0.0.1:5000/login
```
1. Authenticate with an authorized account.
2. Monitor daily vitals and flag patients needing clinical intervention on the **Dashboard**.
3. View longitudinal histories and generate official PDF history summaries under **EHR Records**.
4. Import offline SD card batches under **Import Data**.

---

## 💾 Kiosk SD Card Import Specification

When importing data collected from offline kiosk hardware via `/import`, files can be uploaded as CSV or JSON.

### CSV Column Mapping
The parser supports standard verbose column headers or single-letter hardware codes:

| Letter Code | Verbose Header | Field Description | Example |
|:---:|:---|:---|:---|
| **A** | `Date` | Assessment Date (`YYYY-MM-DD`) | `2026-05-31` |
| **B** | `Time` | Assessment Time (`HH:MM`) | `09:30` |
| **C** | `FirstName` | Patient First Name | `Maria` |
| **D** | `LastName` | Patient Last Name | `Santos` |
| **E** | `Age` | Patient Age (years) | `24` |
| **F** | `Gender` | Gender | `Female` |
| **G** | `BloodPressure`| Blood Pressure (`systolic/diastolic`) | `120/80` |
| **H** | `HeartRate` | Pulse / Heart Rate (BPM) | `78` |
| **I** | `OxygenSaturation` | Oxygen Saturation (%) | `98` |
| **J** | `BodyTemp` | Body Temperature (°C) | `36.7` |
| **K** | `Weight` | Body Weight (kg) | `54.0` |
| **L** | `Height` | Body Height (cm) | `158.0` |
| **M** | `BMI` | Body Mass Index (kg/m²) | `21.6` |

---

## 🔒 Security & Compliance

- **Password Hashing**: Passwords are saved using cryptographic hashes generated by `werkzeug.security`.
- **Role Isolation**: Only accounts with the `System Admin` role can create, update, or remove administrative users.
- **Audit Logging**: Sensitive operations (logins, logouts, patient records additions, updates, imports, and PDF exports) are recorded in the `access_logs` table.
- **Row Level Security (RLS)**: Database tables support fine-grained PostgreSQL security policies configured in Supabase.

---

## 📄 License

This project is developed for academic capstone purposes. All rights reserved by the project authors and institution.
