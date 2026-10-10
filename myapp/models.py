from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date, time, timedelta

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Super Admin'),
        ('HOSPITAL_ADMIN', 'Hospital Admin'),
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient'),
    ]
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    hospital = models.ForeignKey('Hospital', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"


class Specialty(models.Model):
    """Medical specialty / Department domain (e.g. Cardiology, Neurology)"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    icon = models.CharField(max_length=50, default='fa-heartbeat')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Specialties'
        ordering = ['name']

    def __str__(self):
        return self.name


class Hospital(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    city = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=25)
    emergency_helpline = models.CharField(max_length=25)
    email = models.EmailField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.6)
    total_beds = models.PositiveIntegerField(default=150)
    available_icu_beds = models.PositiveIntegerField(default=12)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

    @property
    def doctor_count(self):
        return self.doctors.count()

    @property
    def department_count(self):
        return self.departments.count()


class HospitalDepartment(models.Model):
    """Department setup specifically inside a hospital"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='departments')
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='hospital_departments')
    floor = models.CharField(max_length=50, default='1st Floor')
    head_of_department = models.CharField(max_length=150, blank=True)
    phone_extension = models.CharField(max_length=20, blank=True)
    opd_rooms = models.CharField(max_length=100, default='OPD 101-105')

    class Meta:
        unique_together = ('hospital', 'specialty')

    def __str__(self):
        return f"{self.specialty.name} @ {self.hospital.name}"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='doctors')
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='doctors')
    qualification = models.CharField(max_length=200, default='MBBS, MD')
    experience_years = models.PositiveIntegerField(default=7)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    cabin_number = models.CharField(max_length=50, default='Cabin 102')
    slot_duration_minutes = models.PositiveIntegerField(default=15)  # Required: 15-minute appointments
    start_time = models.TimeField(default=time(9, 0))
    end_time = models.TimeField(default=time(17, 0))
    lunch_start = models.TimeField(default=time(13, 0))
    lunch_end = models.TimeField(default=time(14, 0))
    is_available = models.BooleanField(default=True)
    bio = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.specialty.name})"

    def generate_slots_for_date(self, target_date):
        """Generates all 15-minute time slots for this doctor on the given date,
        marking which slots are already booked to avoid double-booking."""
        slots = []
        current = datetime.combine(target_date, self.start_time)
        end = datetime.combine(target_date, self.end_time)
        lunch_s = datetime.combine(target_date, self.lunch_start)
        lunch_e = datetime.combine(target_date, self.lunch_end)
        step = timedelta(minutes=self.slot_duration_minutes)

        booked_appointments = Appointment.objects.filter(
            doctor=self,
            appointment_date=target_date,
            status__in=['CONFIRMED', 'EMERGENCY_PRIORITY', 'IN_CONSULTATION']
        ).values('id', 'time_slot', 'status', 'token_number', 'patient_name')

        booked_map = {appt['time_slot'].strftime('%H:%M'): appt for appt in booked_appointments}

        while current + step <= end:
            # Skip lunch break
            if not (current >= lunch_s and current < lunch_e):
                slot_time_str = current.time().strftime('%H:%M')
                slot_end_time = (current + step).time()
                is_booked = slot_time_str in booked_map
                appt_info = booked_map.get(slot_time_str)

                slots.append({
                    'time': slot_time_str,
                    'start_time': current.time(),
                    'end_time': slot_end_time,
                    'display': f"{current.strftime('%I:%M %p')} - {(current + step).strftime('%I:%M %p')}",
                    'is_booked': is_booked,
                    'appointment_id': appt_info['id'] if is_booked else None,
                    'status': appt_info['status'] if is_booked else 'AVAILABLE',
                    'token_number': appt_info['token_number'] if is_booked else None,
                    'patient_name': appt_info['patient_name'] if is_booked else None,
                })
            current += step
        return slots


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('EMERGENCY_PRIORITY', 'Emergency Priority'),
        ('IN_CONSULTATION', 'In Consultation'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('SWAPPED', 'Swapped / Rescheduled'),
    ]
    SEVERITY_CHOICES = [
        ('ROUTINE', 'Routine'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
        ('CRITICAL_EMERGENCY', 'Critical Emergency'),
    ]

    token_number = models.PositiveIntegerField()
    token_code = models.CharField(max_length=64, unique=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    patient_name = models.CharField(max_length=150)
    patient_phone = models.CharField(max_length=20)
    patient_age = models.PositiveIntegerField(default=30)
    patient_gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='M')
    
    appointment_date = models.DateField()
    time_slot = models.TimeField()       # Starts at 15-min boundary e.g. 10:15
    end_time_slot = models.TimeField()   # Ends after 15 min e.g. 10:30
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='CONFIRMED')
    is_emergency = models.BooleanField(default=False)
    emergency_severity = models.CharField(max_length=25, choices=SEVERITY_CHOICES, default='ROUTINE')
    emergency_reason = models.TextField(blank=True)
    
    symptoms_summary = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['appointment_date', 'time_slot']

    def __str__(self):
        return f"Token #{self.token_number} - {self.patient_name} with {self.doctor} at {self.time_slot}"

    @property
    def duration_display(self):
        return f"{self.time_slot.strftime('%I:%M %p')} - {self.end_time_slot.strftime('%I:%M %p')} (15 min)"

    @classmethod
    def generate_token(cls, doctor, target_date):
        """Generates next token number and token code for the doctor on date"""
        existing_count = cls.objects.filter(doctor=doctor, appointment_date=target_date).count()
        token_num = existing_count + 1
        code_date = target_date.strftime('%Y%m%d')
        spec_code = doctor.specialty.code[:4].upper()
        hosp_id = doctor.hospital.id
        token_code = f"TK-{hosp_id}-{spec_code}-{code_date}-{token_num:03d}"
        return token_num, token_code


class EmergencySwapLog(models.Model):
    """Audit record when emergency case displaces or swaps with regular appointment"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='swap_logs')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='swap_logs')
    emergency_appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name='swaps_as_emergency'
    )
    displaced_appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='swaps_as_displaced'
    )
    original_slot_time = models.TimeField()
    rescheduled_slot_time = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    swapped_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    swapped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-swapped_at']

    def __str__(self):
        return f"Emergency Swap: {self.emergency_appointment.token_code} displaced {self.displaced_appointment.token_code if self.displaced_appointment else 'Slot'} on {self.swapped_at:%Y-%m-%d %H:%M}"


class PatientVital(models.Model):
    """
    Health Meters Model:
    1. Sugar Meter (Fasting, Postprandial)
    2. Cholesterol Meter (Total, HDL, LDL, Triglycerides)
    3. Overweight / Underweight Meter (BMI, Height, Weight)
    4. Pulse Rate Meter (BPM)
    """
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vitals')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='vitals')
    
    # Blood Sugar (mg/dL)
    sugar_fasting = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    sugar_postprandial = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    sugar_status = models.CharField(max_length=30, blank=True)  # Low, Normal, Pre-diabetic, Diabetic
    
    # Cholesterol (mg/dL)
    cholesterol_total = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    cholesterol_hdl = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    cholesterol_ldl = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    triglycerides = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    cholesterol_status = models.CharField(max_length=30, blank=True)  # Optimal, Borderline, High Risk
    
    # Overweight / Underweight BMI
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    weight_status = models.CharField(max_length=30, blank=True)  # Underweight, Normal, Overweight, Obese
    
    # Pulse Rate (BPM)
    pulse_rate = models.PositiveIntegerField(null=True, blank=True)
    pulse_status = models.CharField(max_length=30, blank=True)  # Bradycardia, Normal, Tachycardia
    
    # Blood Pressure (Optional extra)
    blood_pressure_sys = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_dia = models.PositiveIntegerField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.patient.username} on {self.recorded_at:%Y-%m-%d %H:%M}"

    def calculate_metrics(self):
        """Calculates clinical statuses for Sugar, Cholesterol, BMI, and Pulse Rate"""
        # Sugar analysis
        if self.sugar_fasting is not None:
            val = float(self.sugar_fasting)
            if val < 70:
                self.sugar_status = "Hypoglycemia (Low)"
            elif 70 <= val <= 99:
                self.sugar_status = "Normal (Fasting)"
            elif 100 <= val <= 125:
                self.sugar_status = "Pre-diabetic"
            else:
                self.sugar_status = "Diabetic (High)"
        elif self.sugar_postprandial is not None:
            val = float(self.sugar_postprandial)
            if val < 140:
                self.sugar_status = "Normal (Post-meal)"
            elif 140 <= val <= 199:
                self.sugar_status = "Pre-diabetic (Post-meal)"
            else:
                self.sugar_status = "Diabetic (High)"

        # Cholesterol analysis
        if self.cholesterol_total is not None:
            val = float(self.cholesterol_total)
            if val < 200:
                self.cholesterol_status = "Optimal / Desirable"
            elif 200 <= val <= 239:
                self.cholesterol_status = "Borderline High"
            else:
                self.cholesterol_status = "High Risk"

        # BMI / Weight status
        if self.weight_kg and self.height_cm:
            h_m = float(self.height_cm) / 100.0
            if h_m > 0:
                calc_bmi = float(self.weight_kg) / (h_m * h_m)
                self.bmi = round(calc_bmi, 1)
                if self.bmi < 18.5:
                    self.weight_status = "Underweight"
                elif 18.5 <= self.bmi <= 24.9:
                    self.weight_status = "Normal Weight"
                elif 25.0 <= self.bmi <= 29.9:
                    self.weight_status = "Overweight"
                else:
                    self.weight_status = "Obese"

        # Pulse Rate
        if self.pulse_rate is not None:
            bpm = self.pulse_rate
            if bpm < 60:
                self.pulse_status = "Bradycardia (Low)"
            elif 60 <= bpm <= 100:
                self.pulse_status = "Normal (60-100 BPM)"
            else:
                self.pulse_status = "Tachycardia (High)"


class SymptomCheckRecord(models.Model):
    """Records patient symptom checks and recommendation logs"""
    patient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='symptom_checks')
    symptoms = models.JSONField(default=list)
    severity = models.CharField(max_length=20, default='MODERATE')
    duration = models.CharField(max_length=50, default='1-3 days')
    risk_level = models.CharField(max_length=25, default='LOW')  # LOW, MODERATE, HIGH, CRITICAL_EMERGENCY
    recommended_specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    triage_summary = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Symptom Check ({self.risk_level}) - {self.created_at:%Y-%m-%d %H:%M}"
