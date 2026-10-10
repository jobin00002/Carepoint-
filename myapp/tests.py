from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, time, timedelta, datetime
from myapp.models import (
    UserProfile, Specialty, Hospital, HospitalDepartment, Doctor,
    Appointment, EmergencySwapLog, PatientVital
)

class CarePointHealthcareTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users & Profiles
        self.admin_user = User.objects.create_superuser('admin_test', 'admin@test.com', 'pass123')
        UserProfile.objects.create(user=self.admin_user, role='ADMIN')

        self.patient_user = User.objects.create_user('patient_test', 'patient@test.com', 'pass123')
        UserProfile.objects.create(user=self.patient_user, role='PATIENT', phone='555-0101')

        # Specialty
        self.spec_cardio = Specialty.objects.create(
            name='Cardiology', code='CARD', icon='fa-heart-pulse', description='Cardiovascular medicine'
        )
        self.spec_neuro = Specialty.objects.create(
            name='Neurology', code='NEUR', icon='fa-brain', description='Neurology medicine'
        )

        # Requirement 1: Hospital with specialties
        self.hospital = Hospital.objects.create(
            name='Memorial General Hospital',
            slug='memorial-general-hospital',
            city='Boston',
            address='100 Main St',
            phone='555-1000',
            emergency_helpline='911-0001',
            total_beds=200,
            available_icu_beds=20
        )

        # Requirement 2: Individual Department for Hospital
        self.dept_cardio = HospitalDepartment.objects.create(
            hospital=self.hospital,
            specialty=self.spec_cardio,
            floor='2nd Floor',
            opd_rooms='OPD 201-204',
            head_of_department='Dr. Lead Cardio'
        )

        # Doctor user & Doctor Profile
        self.doctor_user = User.objects.create_user('doctor_test', 'doc@test.com', 'pass123')
        UserProfile.objects.create(user=self.doctor_user, role='DOCTOR', hospital=self.hospital)
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            hospital=self.hospital,
            specialty=self.spec_cardio,
            qualification='MD Cardiology',
            experience_years=10,
            consultation_fee=500.00,
            cabin_number='Cabin 202',
            slot_duration_minutes=15, # Requirement 4: 15 minutes!
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

    def test_requirement_1_hospital_list_and_specialties(self):
        """Requirement 1: Add hospital list with various specialty"""
        response = self.client.get(reverse('hospital_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Memorial General Hospital')
        self.assertContains(response, 'Cardiology')

    def test_requirement_2_department_and_doctor_for_hospital(self):
        """Requirement 2: Individual department and doctor for each hospital"""
        response = self.client.get(reverse('hospital_detail', kwargs={'slug': self.hospital.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cardiology Department')
        self.assertContains(response, 'Cabin 202')
        self.assertContains(response, 'Dr. Lead Cardio')

    def test_requirement_3_and_4_and_6_fifteen_minute_slot_and_avoid_double_booking_and_token(self):
        """
        Requirement 3: Avoid slot booking if already booked
        Requirement 4: Schedule each appointment for 15 minutes
        Requirement 6: Give token number to patients for each booking
        """
        self.client.login(username='patient_test', password='pass123')
        target_date = date.today()

        # First booking at 09:00 (15 minutes)
        response = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.id,
            'appointment_date': target_date.strftime('%Y-%m-%d'),
            'time_slot': '09:00',
            'patient_name': 'Test Patient 1',
            'patient_phone': '555-1111',
            'patient_age': 35,
            'patient_gender': 'M',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        appt1 = Appointment.objects.get(patient_name='Test Patient 1')
        
        # Requirement 4 check: Duration is exactly 15 minutes (09:00 to 09:15)
        self.assertEqual(appt1.time_slot, time(9, 0))
        self.assertEqual(appt1.end_time_slot, time(9, 15))
        
        # Requirement 6 check: Token number and unique token code
        self.assertEqual(appt1.token_number, 1)
        self.assertTrue(appt1.token_code.startswith('TK-'))
        self.assertIn('#1', response.content.decode())

        # Requirement 3 check: Attempt to double-book the same 09:00 slot with routine appointment
        response_double = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.id,
            'appointment_date': target_date.strftime('%Y-%m-%d'),
            'time_slot': '09:00',
            'patient_name': 'Test Patient 2',
            'patient_phone': '555-2222',
            'patient_age': 40,
            'patient_gender': 'F',
            'is_emergency': '0',
        }, follow=True)

        # Must reject and show already booked warning
        self.assertContains(response_double, 'already booked')
        # Patient 2 must NOT have been booked at 09:00
        self.assertFalse(Appointment.objects.filter(patient_name='Test Patient 2').exists())

    def test_requirement_5_emergency_swap(self):
        """Requirement 5: Swap appointment if there are any emergency cases"""
        self.client.login(username='patient_test', password='pass123')
        target_date = date.today()

        # Regular patient booked at 09:00
        appt_regular = Appointment.objects.create(
            token_number=1,
            token_code='TK-TEST-001',
            doctor=self.doctor,
            patient=self.patient_user,
            patient_name='Routine Patient',
            patient_phone='555-0011',
            appointment_date=target_date,
            time_slot=time(9, 0),
            end_time_slot=time(9, 15),
            status='CONFIRMED',
        )

        # Emergency patient arrives needing 09:00 slot
        response_emerg = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.id,
            'appointment_date': target_date.strftime('%Y-%m-%d'),
            'time_slot': '09:00',
            'patient_name': 'Emergency Patient',
            'patient_phone': '555-9999',
            'patient_age': 60,
            'patient_gender': 'M',
            'is_emergency': '1',
            'emergency_severity': 'CRITICAL_EMERGENCY',
            'symptoms': 'Acute chest pressure',
        }, follow=True)

        self.assertEqual(response_emerg.status_code, 200)

        # Check emergency appointment took 09:00
        emerg_appt = Appointment.objects.get(patient_name='Emergency Patient')
        self.assertEqual(emerg_appt.time_slot, time(9, 0))
        self.assertEqual(emerg_appt.status, 'EMERGENCY_PRIORITY')
        self.assertTrue(emerg_appt.is_emergency)

        # Check displaced regular patient was swapped to next slot
        appt_regular.refresh_from_db()
        self.assertEqual(appt_regular.status, 'SWAPPED')
        self.assertNotEqual(appt_regular.time_slot, time(9, 0))

        # Check swap was recorded in EmergencySwapLog
        swap_log = EmergencySwapLog.objects.filter(emergency_appointment=emerg_appt).first()
        self.assertIsNotNone(swap_log)
        self.assertEqual(swap_log.original_slot_time, time(9, 0))

    def test_requirement_7_health_meters(self):
        """Requirement 7: Meter of sugar, cholesterol, overweight/underweight, pulse rate"""
        vital = PatientVital(
            patient=self.patient_user,
            sugar_fasting=108.0,      # Pre-diabetes (100-125)
            cholesterol_total=245.0,  # High Risk (>=240)
            weight_kg=85.0,
            height_cm=170.0,          # BMI = 29.4 (Overweight)
            pulse_rate=115,           # Tachycardia (>100)
        )
        vital.calculate_metrics()
        vital.save()

        self.assertEqual(vital.sugar_status, 'Pre-diabetic')
        self.assertEqual(vital.cholesterol_status, 'High Risk')
        self.assertEqual(vital.bmi, 29.4)
        self.assertEqual(vital.weight_status, 'Overweight')
        self.assertEqual(vital.pulse_status, 'Tachycardia (High)')

        # Test view render
        self.client.login(username='patient_test', password='pass123')
        response = self.client.get(reverse('health_meters'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blood Sugar Meter')
        self.assertContains(response, 'Cholesterol Meter')
        self.assertContains(response, 'Overweight / Underweight Meter')
        self.assertContains(response, 'Pulse Rate Meter')

    def test_portals_access(self):
        """Test access to 4 separate portals"""
        # Admin Portal
        self.client.login(username='admin_test', password='pass123')
        resp = self.client.get(reverse('admin_portal'))
        self.assertEqual(resp.status_code, 200)

        # Patient Portal
        self.client.login(username='patient_test', password='pass123')
        resp = self.client.get(reverse('patient_portal'))
        self.assertEqual(resp.status_code, 200)

        # Doctor Portal
        self.client.login(username='doctor_test', password='pass123')
        resp = self.client.get(reverse('doctor_portal'))
        self.assertEqual(resp.status_code, 200)

    def test_separate_login_and_register_pages(self):
        """Test separate login and register pages and verify no register page for admin"""
        # 1. Admin login exists, but NO admin register exists
        resp_admin_login = self.client.get(reverse('admin_login'))
        self.assertEqual(resp_admin_login.status_code, 200)
        self.assertContains(resp_admin_login, 'Central Admin Sign In')
        
        # Verify no admin register route exists
        resp_no_admin_reg = self.client.get('/admin-register/')
        self.assertEqual(resp_no_admin_reg.status_code, 404)

        # 2. Hospital separate login & register
        resp_hosp_login = self.client.get(reverse('hospital_login'))
        self.assertEqual(resp_hosp_login.status_code, 200)
        resp_hosp_reg = self.client.get(reverse('hospital_register'))
        self.assertEqual(resp_hosp_reg.status_code, 200)

        # 3. Doctor separate login & register
        resp_doc_login = self.client.get(reverse('doctor_login'))
        self.assertEqual(resp_doc_login.status_code, 200)
        resp_doc_reg = self.client.get(reverse('doctor_register'))
        self.assertEqual(resp_doc_reg.status_code, 200)

        # 4. Patient separate login & register
        resp_pat_login = self.client.get(reverse('patient_login'))
        self.assertEqual(resp_pat_login.status_code, 200)
        resp_pat_reg = self.client.get(reverse('patient_register'))
        self.assertEqual(resp_pat_reg.status_code, 200)
