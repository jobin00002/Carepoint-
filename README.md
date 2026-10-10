# CarePoint - Smart Healthcare Appointment & Clinical Triage System

CarePoint is a full-featured, production-ready web application built with **Django** and modern responsive UI components. It features **4 separate dedicated portals** (Admin, Hospital, Doctor, and Patient) along with an intelligent **Symptom Checker**, **15-Minute Slot Scheduling Engine**, **Zero Double-Booking Guarantee**, **Emergency Priority Swap Protocol**, **Digital Patient Token Passes**, and interactive **Health Vital Meters** (Blood Sugar, Cholesterol, BMI Overweight/Underweight, and Pulse Rate).

---

## 🌟 Key Features & Requirements

### 1. Hospital List with Various Specialties
* Browse accredited multi-specialty hospitals with capacity metrics (Total Beds, Available ICU Beds).
* Filter hospitals by **Specialty** (Cardiology, Neurology, Orthopedics, Pediatrics, Dermatology, Gastroenterology, General Medicine, ENT, Emergency Medicine) or search by city and keywords.
* Direct access to hospital profiles and emergency telephone links.

### 2. Individual Departments and Doctors for Each Hospital
* Each hospital features individual clinical departments with assigned Floor locations, OPD Room suites, and Department Heads (HOD).
* Doctors are assigned specifically to departments within hospitals, displaying qualifications, clinical experience, consultation fees, and assigned cabin numbers.

### 3. Avoid Slot Booking If Already Booked (Zero Double-Booking)
* 15-minute consultation slots are tracked in real-time.
* Already booked slots are visually locked and disabled (`.slot-pill.booked`) in the interactive calendar grid.
* Server-side database transactions (`select_for_update` / atomic locking) strictly block race conditions and duplicate bookings.

### 4. Schedule Each Appointment for 15 Minutes
* Appointments are strictly generated and booked in **15-minute blocks** (e.g. `09:00 - 09:15`, `09:15 - 09:30`, `09:30 - 09:45`).
* Timetable displays clear 15-minute time badges on both patient booking and doctor schedule views.

### 5. Emergency Priority Slot Swap Engine
* Critical emergency patients (severe trauma, acute chest pain, stroke symptoms) can be prioritized into booked slots.
* The system automatically swaps the emergency patient into the priority slot, and automatically reschedules the displaced patient into the next available 15-minute slot.
* Every swap is logged into the `EmergencySwapLog` audit trail with timestamp, reasons, and authorized user.
* Both Doctor and Hospital portals include dedicated **Emergency Slot Swap Desks**.

### 6. Digital Patient Token Number for Each Booking
* Each confirmed appointment generates a sequential **Token Number** (e.g., `#1`, `#2`, `#3`) and unique identifier (`TK-HOSP-SPEC-YYYYMMDD-00X`).
* Features a printable **Digital Token Pass** with simulated QR code and a **Live Queue Tracker** showing:
  - *Current Token Being Served in Cabin*
  - *Tokens Ahead in Line*
  - *Estimated Wait Time in Minutes*

### 7. Interactive Health Meters Suite (Sugar, Cholesterol, BMI, Pulse Rate)
* **Blood Sugar Meter (Glucose mg/dL):** Semicircular SVG dial with needle deflection for Fasting (70-99 Normal, 100-125 Pre-diabetic, ≥126 Diabetic) and Post-prandial ranges.
* **Cholesterol Meter (Total Lipids mg/dL):** Speedometer gauge with NCEP ATP III thresholds (Desirable <200, Borderline 200-239, High Risk ≥240).
* **Overweight / Underweight Meter (BMI):** Dynamic BMI gauge calculating Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), and Obese (≥30) with recommended Ideal Body Weight range based on height.
* **Pulse Rate Meter (Heart Rate BPM):** Animated pulsating heart icon that beats at the exact frequency of the measured heart rate, with needle gauge showing Bradycardia (<60), Normal (60-100), and Tachycardia (>100).
* Patients can save their meter readings into their medical profile for doctor review.

---

## 🚪 Dedicated Role-Based Portals (Separate Login & Registration)

Each portal now has its own dedicated, secure Login and Registration pages (Admin has **Login only**; no registration page exists for Admin):

| Portal | Dedicated Login URL | Dedicated Register URL | Description |
|---|---|---|---|
| **Central Admin Portal** | [`/admin-login/`](http://127.0.0.1:8000/admin-login/) | *(None - Admin login only)* | System analytics, hospitals roster, doctor credentials, and Emergency Swap audit registry. |
| **Hospital Portal** | [`/hospital-login/`](http://127.0.0.1:8000/hospital-login/) | [`/hospital-register/`](http://127.0.0.1:8000/hospital-register/) | Hospital management: register new hospital, manage clinical departments, resident doctors, OPD queue, and emergency swaps. |
| **Doctor Portal** | [`/doctor-login/`](http://127.0.0.1:8000/doctor-login/) | [`/doctor-register/`](http://127.0.0.1:8000/doctor-register/) | Doctor schedule: live 15-minute slot timetable, Token Desk (*Call Next*, *In Consultation*, *Completed*), patient vitals inspection. |
| **Patient Portal** | [`/patient-login/`](http://127.0.0.1:8000/patient-login/) | [`/patient-register/`](http://127.0.0.1:8000/patient-register/) | Patient profile: view booked appointments, download digital token passes, review symptom triage history, and log health meters. |
| **Portal Hub / Chooser** | [`/portal-select/`](http://127.0.0.1:8000/portal-select/) | — | Clean portal selection landing page directing users to their respective portal sign-in/registration. |

---

## 🚀 Running the Project

```bash
# Navigate to the Django project folder
cd carepoint

# Apply migrations
..\venv\Scripts\python.exe manage.py migrate

# Seed realistic demo data (hospitals, doctors, appointments, vitals, demo users)
..\venv\Scripts\python.exe manage.py seed_data

# Run tests
..\venv\Scripts\python.exe manage.py test

# Start development server
..\venv\Scripts\python.exe manage.py runserver
```

Visit in your web browser: **`http://127.0.0.1:8000/`**
