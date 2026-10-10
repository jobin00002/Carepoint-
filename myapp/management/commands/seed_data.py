from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta, datetime
from myapp.models import (
    UserProfile, Specialty, Hospital, HospitalDepartment, Doctor,
    Appointment, EmergencySwapLog, PatientVital
)

class Command(BaseCommand):
    help = 'Seeds database with realistic hospitals, departments, doctors, appointments, vitals, and portal users'

    def handle(self, *args, **options):
        self.stdout.write("Seeding CarePoint database...")

        # 1. Superuser / Admin
        admin_user, _ = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@carepoint.health',
            'first_name': 'Chief',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
        })
        admin_user.set_password('admin123')
        admin_user.save()
        UserProfile.objects.get_or_create(user=admin_user, defaults={
            'role': 'ADMIN',
            'phone': '+1 (800) 555-0100',
        })

        # 2. Specialties
        specialties_data = [
            ('Cardiology', 'CARD', 'fa-heart-pulse', 'Heart conditions, hypertension, arrhythmias, coronary artery care, and cardiovascular surgery.'),
            ('Neurology', 'NEUR', 'fa-brain', 'Brain disorders, stroke management, seizures, migraines, and peripheral nervous system.'),
            ('Orthopedics', 'ORTH', 'fa-bone', 'Bone fractures, joint replacements, sports injuries, spine disorders, and arthritis care.'),
            ('Pediatrics', 'PEDI', 'fa-baby', 'Child healthcare, vaccinations, pediatric infectious diseases, and developmental care.'),
            ('General Medicine', 'GMED', 'fa-stethoscope', 'Primary care, fever, seasonal flu, lifestyle diseases, diabetes, and preventive checkups.'),
            ('Dermatology', 'DERM', 'fa-hand-dots', 'Skin diseases, acne, eczema, psoriasis, hair loss, and cosmetic dermatology.'),
            ('Gastroenterology', 'GAST', 'fa-virus', 'Digestive tract, liver disorders, endoscopy, gastritis, and inflammatory bowel diseases.'),
            ('ENT (Otolaryngology)', 'ENT', 'fa-ear-listen', 'Ear infections, hearing loss, sinus problems, throat pain, and tonsillitis.'),
            ('Emergency Medicine', 'EMER', 'fa-truck-medical', 'Critical trauma, acute cardiac arrest, respiratory failure, and urgent 24/7 care.'),
        ]
        spec_objs = {}
        for name, code, icon, desc in specialties_data:
            s, _ = Specialty.objects.update_or_create(
                code=code,
                defaults={'name': name, 'icon': icon, 'description': desc}
            )
            spec_objs[code] = s

        # 3. Hospitals (Requirement 1: Hospital list with various specialties)
        hospitals_data = [
            {
                'name': 'City General Multi-Specialty Hospital',
                'slug': 'city-general-hospital',
                'city': 'New York',
                'address': '450 Lexington Ave, Manhattan, NY 10017',
                'phone': '+1 (212) 555-0145',
                'emergency_helpline': '+1 (212) 555-9911',
                'email': 'info@citygeneral.health',
                'rating': 4.8,
                'total_beds': 350,
                'available_icu_beds': 28,
                'description': 'Premier multi-specialty trauma and tertiary care medical facility equipped with advanced robotics, 24/7 ICU, and expert clinical departments.',
                'image_url': 'https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&w=800&q=80',
                'specs': ['CARD', 'NEUR', 'ORTH', 'PEDI', 'GMED', 'EMER', 'GAST'],
            },
            {
                'name': 'Apollo Care Super-Specialty Medical Center',
                'slug': 'apollo-care-medical-center',
                'city': 'Chicago',
                'address': '820 N Michigan Ave, Chicago, IL 60611',
                'phone': '+1 (312) 555-0188',
                'emergency_helpline': '+1 (312) 555-9111',
                'email': 'contact@apollocare.health',
                'rating': 4.7,
                'total_beds': 280,
                'available_icu_beds': 22,
                'description': 'Nationally ranked center of excellence for cardiac surgery, neuroscience, dermatology, and comprehensive gastroenterology.',
                'image_url': 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=800&q=80',
                'specs': ['CARD', 'NEUR', 'DERM', 'ENT', 'GMED'],
            },
            {
                'name': 'St. Jude Family Hospital & Trauma Center',
                'slug': 'st-jude-family-hospital',
                'city': 'Los Angeles',
                'address': '1200 Wilshire Blvd, Los Angeles, CA 90017',
                'phone': '+1 (213) 555-0199',
                'emergency_helpline': '+1 (213) 555-9999',
                'email': 'care@stjudefamily.health',
                'rating': 4.9,
                'total_beds': 220,
                'available_icu_beds': 18,
                'description': 'Community-focused hospital recognized for family healthcare, pediatric excellence, orthopedic rehabilitation, and urgent trauma triage.',
                'image_url': 'https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=800&q=80',
                'specs': ['PEDI', 'ORTH', 'GMED', 'EMER', 'DERM'],
            },
            {
                'name': 'Metro Heart & Neuro Advanced Institute',
                'slug': 'metro-heart-neuro-institute',
                'city': 'San Francisco',
                'address': '500 Parnassus Ave, San Francisco, CA 94143',
                'phone': '+1 (415) 555-0122',
                'emergency_helpline': '+1 (415) 555-9112',
                'email': 'sf@metroheartneuro.health',
                'rating': 4.9,
                'total_beds': 190,
                'available_icu_beds': 25,
                'description': 'Super-specialized research institute dedicated to cutting-edge interventional cardiology, neurovascular surgery, and stroke rehabilitation.',
                'image_url': 'https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=800&q=80',
                'specs': ['CARD', 'NEUR', 'GMED'],
            },
        ]

        hosp_objs = {}
        for hdata in hospitals_data:
            h, _ = Hospital.objects.update_or_create(
                slug=hdata['slug'],
                defaults={
                    'name': hdata['name'],
                    'city': hdata['city'],
                    'address': hdata['address'],
                    'phone': hdata['phone'],
                    'emergency_helpline': hdata['emergency_helpline'],
                    'email': hdata['email'],
                    'rating': hdata['rating'],
                    'total_beds': hdata['total_beds'],
                    'available_icu_beds': hdata['available_icu_beds'],
                    'description': hdata['description'],
                    'image_url': hdata['image_url'],
                }
            )
            hosp_objs[h.slug] = h

            # Requirement 2: Add individual departments for each hospital
            for code in hdata['specs']:
                spec = spec_objs[code]
                HospitalDepartment.objects.get_or_create(
                    hospital=h, specialty=spec,
                    defaults={
                        'floor': f"Floor {(list(hdata['specs']).index(code) % 4) + 1}",
                        'head_of_department': f"Dr. Lead {spec.name}",
                        'opd_rooms': f"OPD {100 + list(hdata['specs']).index(code)*5}-{104 + list(hdata['specs']).index(code)*5}",
                        'phone_extension': f"Ext {400 + list(hdata['specs']).index(code)}",
                    }
                )

        # 4. Hospital Admin User
        metro_hosp = hosp_objs['city-general-hospital']
        hosp_user, _ = User.objects.get_or_create(username='metro_admin', defaults={
            'email': 'admin@citygeneral.health',
            'first_name': 'Marcus',
            'last_name': 'Vance',
        })
        hosp_user.set_password('metro123')
        hosp_user.save()
        UserProfile.objects.update_or_create(
            user=hosp_user,
            defaults={
                'role': 'HOSPITAL_ADMIN',
                'hospital': metro_hosp,
                'phone': '+1 (212) 555-0146',
            }
        )

        # 5. Doctors for each Hospital & Department (Requirement 2)
        doctors_data = [
            # City General
            {
                'username': 'dr_sarah', 'first_name': 'Sarah', 'last_name': 'Jenkins',
                'email': 'sarah.jenkins@citygeneral.health', 'hospital': metro_hosp,
                'specialty': spec_objs['CARD'], 'qualification': 'MD, FACC (Interventional Cardiology)',
                'experience': 14, 'fee': 650.00, 'cabin': 'Room 204 (Heart Center)',
                'bio': 'Board-certified cardiologist specializing in preventive cardiology, coronary angioplasty, and hypertension management with over 14 years of clinical experience.'
            },
            {
                'username': 'dr_rajesh', 'first_name': 'Rajesh', 'last_name': 'Sharma',
                'email': 'rajesh.sharma@citygeneral.health', 'hospital': metro_hosp,
                'specialty': spec_objs['NEUR'], 'qualification': 'MD, DM (Neurology)',
                'experience': 11, 'fee': 700.00, 'cabin': 'Room 310 (Neuro Wing)',
                'bio': 'Expert neurologist focusing on acute stroke intervention, chronic migraine therapy, and peripheral nerve disorders.'
            },
            {
                'username': 'dr_david', 'first_name': 'David', 'last_name': 'Miller',
                'email': 'david.miller@citygeneral.health', 'hospital': metro_hosp,
                'specialty': spec_objs['ORTH'], 'qualification': 'MS (Orthopedics), MCh (Joint Recon)',
                'experience': 12, 'fee': 600.00, 'cabin': 'Room 105 (Bone & Joint Wing)',
                'bio': 'Orthopedic specialist in minimally invasive knee and hip joint reconstruction, arthroscopy, and sports injury recovery.'
            },
            {
                'username': 'dr_emily', 'first_name': 'Emily', 'last_name': 'Carter',
                'email': 'emily.carter@citygeneral.health', 'hospital': metro_hosp,
                'specialty': spec_objs['GMED'], 'qualification': 'MD (Internal Medicine)',
                'experience': 8, 'fee': 450.00, 'cabin': 'Room 101 (General OPD)',
                'bio': 'Compassionate physician treating systemic disorders, infectious fevers, diabetes mellitus, and comprehensive executive wellness.'
            },
            # Apollo Care
            {
                'username': 'dr_michael', 'first_name': 'Michael', 'last_name': 'Chen',
                'email': 'm.chen@apollocare.health', 'hospital': hosp_objs['apollo-care-medical-center'],
                'specialty': spec_objs['CARD'], 'qualification': 'MD, PhD (Cardiology)',
                'experience': 16, 'fee': 750.00, 'cabin': 'Cabin 401 (Cardiac OPD)',
                'bio': 'Leading cardiologist in electrophysiology, arrhythmia diagnosis, pacemaker implantation, and cardiac ultrasound.'
            },
            {
                'username': 'dr_olivia', 'first_name': 'Olivia', 'last_name': 'Taylor',
                'email': 'o.taylor@apollocare.health', 'hospital': hosp_objs['apollo-care-medical-center'],
                'specialty': spec_objs['DERM'], 'qualification': 'MD (Dermatology, Venereology)',
                'experience': 9, 'fee': 500.00, 'cabin': 'Cabin 202 (Skin Care Clinic)',
                'bio': 'Dermatologist offering advanced laser treatments, autoimmune skin condition management, psoriasis, and clinical acne solutions.'
            },
            # St. Jude
            {
                'username': 'dr_sophia', 'first_name': 'Sophia', 'last_name': 'Rodriguez',
                'email': 's.rodriguez@stjudefamily.health', 'hospital': hosp_objs['st-jude-family-hospital'],
                'specialty': spec_objs['PEDI'], 'qualification': 'MD (Pediatrics), FAAP',
                'experience': 10, 'fee': 550.00, 'cabin': 'Room 108 (Children Wing)',
                'bio': 'Dedicated pediatrician passionate about neonatal intensive care, child immunization schedules, allergy therapy, and growth monitoring.'
            },
            # Metro Heart & Neuro
            {
                'username': 'dr_alex', 'first_name': 'Alexander', 'last_name': 'Wright',
                'email': 'a.wright@metroheartneuro.health', 'hospital': hosp_objs['metro-heart-neuro-institute'],
                'specialty': spec_objs['NEUR'], 'qualification': 'MD, Fellowship in Neurovascular Care',
                'experience': 15, 'fee': 800.00, 'cabin': 'Room 502 (Cerebrovascular OPD)',
                'bio': 'Recognized specialist in neurovascular care, brain aneurysm evaluations, epilepsy management, and neurological sleep disorders.'
            },
        ]

        dr_sarah_obj = None
        for d in doctors_data:
            user, _ = User.objects.get_or_create(username=d['username'], defaults={
                'email': d['email'],
                'first_name': d['first_name'],
                'last_name': d['last_name'],
            })
            user.set_password('doctor123')
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': 'DOCTOR',
                    'hospital': d['hospital'],
                    'phone': '+1 (555) 234-8900',
                }
            )

            doc, _ = Doctor.objects.update_or_create(
                user=user,
                defaults={
                    'hospital': d['hospital'],
                    'specialty': d['specialty'],
                    'qualification': d['qualification'],
                    'experience_years': d['experience'],
                    'consultation_fee': d['fee'],
                    'cabin_number': d['cabin'],
                    'slot_duration_minutes': 15,  # 15 minutes requirement!
                    'start_time': time(9, 0),
                    'end_time': time(17, 0),
                    'lunch_start': time(13, 0),
                    'lunch_end': time(14, 0),
                    'bio': d['bio'],
                }
            )
            if d['username'] == 'dr_sarah':
                dr_sarah_obj = doc

        # 6. Patients
        patient_user, _ = User.objects.get_or_create(username='patient_john', defaults={
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
        })
        patient_user.set_password('patient123')
        patient_user.save()
        UserProfile.objects.update_or_create(
            user=patient_user,
            defaults={
                'role': 'PATIENT',
                'phone': '+1 (555) 789-1234',
                'gender': 'M',
                'date_of_birth': date(1988, 5, 14),
                'blood_group': 'O+',
                'address': '124 Elm Street, Apt 4B, Brooklyn, NY',
            }
        )

        patient2, _ = User.objects.get_or_create(username='patient_alice', defaults={
            'email': 'alice.smith@example.com',
            'first_name': 'Alice',
            'last_name': 'Smith',
        })
        patient2.set_password('patient123')
        patient2.save()
        UserProfile.objects.update_or_create(
            user=patient2,
            defaults={
                'role': 'PATIENT',
                'phone': '+1 (555) 456-7890',
                'gender': 'F',
                'date_of_birth': date(1993, 11, 2),
                'blood_group': 'A+',
                'address': '78 Queens Blvd, Queens, NY',
            }
        )

        # 7. Pre-seed Booked Appointments for Today (To test 15-min slots, tokens, and avoidance of double-booking)
        today = date.today()
        if dr_sarah_obj:
            # Clear previous test appointments for clean test run
            Appointment.objects.filter(doctor=dr_sarah_obj, appointment_date=today).delete()

            # Slot 1: 09:00 - 09:15
            t1, c1 = Appointment.generate_token(dr_sarah_obj, today)
            Appointment.objects.create(
                token_number=1,
                token_code=c1,
                doctor=dr_sarah_obj,
                patient=patient_user,
                patient_name="John Doe",
                patient_phone="+1 (555) 789-1234",
                patient_age=36,
                patient_gender="M",
                appointment_date=today,
                time_slot=time(9, 0),
                end_time_slot=time(9, 15),
                status='IN_CONSULTATION',
                symptoms_summary="Routine hypertension follow-up and ECG check",
            )

            # Slot 2: 09:15 - 09:30
            t2, c2 = Appointment.generate_token(dr_sarah_obj, today)
            Appointment.objects.create(
                token_number=2,
                token_code=c2,
                doctor=dr_sarah_obj,
                patient=patient2,
                patient_name="Alice Smith",
                patient_phone="+1 (555) 456-7890",
                patient_age=31,
                patient_gender="F",
                appointment_date=today,
                time_slot=time(9, 15),
                end_time_slot=time(9, 30),
                status='CONFIRMED',
                symptoms_summary="Occasional palpitations after heavy exercise",
            )

            # Slot 3: 09:30 - 09:45
            t3, c3 = Appointment.generate_token(dr_sarah_obj, today)
            displaced_appt = Appointment.objects.create(
                token_number=3,
                token_code=c3,
                doctor=dr_sarah_obj,
                patient=patient_user,
                patient_name="Robert Williams",
                patient_phone="+1 (555) 321-6543",
                patient_age=52,
                patient_gender="M",
                appointment_date=today,
                time_slot=time(9, 30),
                end_time_slot=time(9, 45),
                status='CONFIRMED',
                symptoms_summary="Cholesterol medication review",
            )

            # Pre-seed an Emergency Swap example (Requirement 5)
            # Emergency patient arrives needing priority slot
            t4, c4 = Appointment.generate_token(dr_sarah_obj, today)
            emergency_appt = Appointment.objects.create(
                token_number=4,
                token_code=c4,
                doctor=dr_sarah_obj,
                patient=patient2,
                patient_name="James Miller (Emergency)",
                patient_phone="+1 (555) 999-4321",
                patient_age=58,
                patient_gender="M",
                appointment_date=today,
                time_slot=time(9, 45),
                end_time_slot=time(10, 0),
                status='EMERGENCY_PRIORITY',
                is_emergency=True,
                emergency_severity='CRITICAL_EMERGENCY',
                symptoms_summary="Acute crushing chest pain, diaphoresis, radiating to jaw",
                emergency_reason="Immediate triage required for suspected acute coronary syndrome",
            )

            EmergencySwapLog.objects.create(
                hospital=metro_hosp,
                doctor=dr_sarah_obj,
                emergency_appointment=emergency_appt,
                displaced_appointment=displaced_appt,
                original_slot_time=time(9, 30),
                rescheduled_slot_time=time(10, 0),
                reason="Preempted for suspected acute myocardial infarction triage.",
                swapped_by=admin_user,
            )

        # 8. Pre-seed Patient Vitals with Sugar, Cholesterol, BMI, and Pulse Rate (Requirement 7)
        PatientVital.objects.filter(patient=patient_user).delete()
        v1 = PatientVital(
            patient=patient_user,
            sugar_fasting=94.0,           # Normal
            sugar_postprandial=132.0,     # Normal
            cholesterol_total=185.0,      # Desirable (<200)
            cholesterol_hdl=54.0,
            cholesterol_ldl=108.0,
            triglycerides=115.0,
            weight_kg=72.5,               # Height 175cm -> BMI 23.7 (Normal)
            height_cm=175.0,
            pulse_rate=72,                # Normal (60-100 BPM)
            blood_pressure_sys=120,
            blood_pressure_dia=80,
            notes="Morning baseline reading: all parameters optimal.",
        )
        v1.calculate_metrics()
        v1.save()

        # Older record showing borderline cholesterol
        v2 = PatientVital(
            patient=patient_user,
            sugar_fasting=108.0,          # Pre-diabetic (100-125)
            cholesterol_total=225.0,      # Borderline High (200-239)
            weight_kg=78.0,               # BMI 25.5 (Overweight)
            height_cm=175.0,
            pulse_rate=88,                # Normal
            notes="Previous month checkup: borderline cholesterol and elevated fasting glucose.",
        )
        v2.calculate_metrics()
        v2.save()

        self.stdout.write(self.style.SUCCESS("CarePoint database seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("Demo Accounts Created:"))
        self.stdout.write(self.style.SUCCESS("  1. Super Admin: admin / admin123"))
        self.stdout.write(self.style.SUCCESS("  2. Hospital Admin: metro_admin / metro123"))
        self.stdout.write(self.style.SUCCESS("  3. Doctor: dr_sarah / doctor123"))
        self.stdout.write(self.style.SUCCESS("  4. Patient: patient_john / patient123"))
