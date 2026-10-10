import json
from datetime import datetime, date, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Count, Q

from .models import (
    UserProfile, Specialty, Hospital, HospitalDepartment, Doctor,
    Appointment, EmergencySwapLog, PatientVital, SymptomCheckRecord
)

# ----------------- Decorators & Helpers -----------------

def role_required(allowed_roles):
    """Decorator to enforce role-based portal access"""
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            user_role = profile.role if profile else ('ADMIN' if request.user.is_superuser else 'PATIENT')
            if request.user.is_superuser or user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Access denied: You do not have permission for this portal.")
            return redirect('dashboard_redirect')
        return _wrapped_view
    return decorator


def dashboard_redirect(request):
    """Redirects authenticated users to their corresponding portal"""
    if not request.user.is_authenticated:
        return redirect('login')
    profile = getattr(request.user, 'profile', None)
    if request.user.is_superuser or (profile and profile.role == 'ADMIN'):
        return redirect('admin_portal')
    elif profile and profile.role == 'HOSPITAL_ADMIN':
        return redirect('hospital_portal')
    elif profile and profile.role == 'DOCTOR':
        return redirect('doctor_portal')
    else:
        return redirect('patient_portal')


# ----------------- Authentication Views -----------------

# ----------------- Separate Authentication Views -----------------

def portal_select_view(request):
    """Unified portal chooser allowing users to navigate to their dedicated portal login/register."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    return render(request, 'auth/portal_select.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')


# 1. Admin Login (Notice: NO registration page for admin!)
def admin_login_view(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if request.user.is_superuser or (profile and profile.role == 'ADMIN'):
            return redirect('admin_portal')
        messages.warning(request, "You are logged in as a non-admin user. Sign out first to access Admin Portal.")
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            profile = getattr(user, 'profile', None)
            if user.is_superuser or (profile and profile.role == 'ADMIN'):
                login(request, user)
                messages.success(request, f"Welcome to Central Admin Portal, {user.get_full_name() or user.username}!")
                return redirect('admin_portal')
            else:
                messages.error(request, "Access Denied: This account does not possess Administrator privileges.")
        else:
            messages.error(request, "Invalid administrator username or password.")
    return render(request, 'auth/admin_login.html')


# 2. Hospital Portal Login & Register
def hospital_login_view(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'HOSPITAL_ADMIN':
            return redirect('hospital_portal')
        elif request.user.is_superuser or (profile and profile.role == 'ADMIN'):
            return redirect('hospital_portal')
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            profile = getattr(user, 'profile', None)
            if user.is_superuser or (profile and profile.role in ['HOSPITAL_ADMIN', 'ADMIN']):
                login(request, user)
                messages.success(request, f"Welcome to Hospital Management Portal, {user.get_full_name() or user.username}!")
                return redirect('hospital_portal')
            else:
                messages.error(request, "Access Denied: This account is not a Hospital Administrator.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'auth/hospital_login.html')


def hospital_register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Hospital Info
        hospital_name = request.POST.get('hospital_name', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()
        hospital_phone = request.POST.get('hospital_phone', '').strip()
        emergency_helpline = request.POST.get('emergency_helpline', '').strip()
        total_beds = int(request.POST.get('total_beds', 100))
        available_icu_beds = int(request.POST.get('available_icu_beds', 10))
        description = request.POST.get('description', '').strip()

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/hospital_register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'auth/hospital_register.html')

        from django.utils.text import slugify
        slug = slugify(hospital_name)
        if Hospital.objects.filter(slug=slug).exists():
            slug = f"{slug}-{User.objects.count() + 1}"

        with transaction.atomic():
            hospital = Hospital.objects.create(
                name=hospital_name,
                slug=slug,
                city=city,
                address=address,
                phone=hospital_phone,
                emergency_helpline=emergency_helpline,
                total_beds=total_beds,
                available_icu_beds=available_icu_beds,
                description=description
            )
            gmed = Specialty.objects.filter(code='GMED').first()
            if gmed:
                HospitalDepartment.objects.get_or_create(hospital=hospital, specialty=gmed, defaults={'floor': '1st Floor'})

            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            UserProfile.objects.create(
                user=user, role='HOSPITAL_ADMIN', hospital=hospital, phone=phone
            )

        login(request, user)
        messages.success(request, f"Hospital '{hospital.name}' registered successfully! Welcome to your Hospital Portal.")
        return redirect('hospital_portal')

    return render(request, 'auth/hospital_register.html')


# 3. Doctor Portal Login & Register
def doctor_login_view(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'DOCTOR':
            return redirect('doctor_portal')
        elif request.user.is_superuser or (profile and profile.role == 'ADMIN'):
            return redirect('doctor_portal')
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            profile = getattr(user, 'profile', None)
            if user.is_superuser or (profile and profile.role in ['DOCTOR', 'ADMIN']):
                login(request, user)
                messages.success(request, f"Welcome back, Dr. {user.get_full_name() or user.username}!")
                return redirect('doctor_portal')
            else:
                messages.error(request, "Access Denied: This account is not registered as a Doctor.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'auth/doctor_login.html')


def doctor_register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    hospitals = Hospital.objects.all()
    specialties = Specialty.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()

        hospital_id = request.POST.get('hospital')
        specialty_id = request.POST.get('specialty')
        qualification = request.POST.get('qualification', 'MBBS, MD').strip()
        experience_years = int(request.POST.get('experience_years', 5))
        consultation_fee = float(request.POST.get('consultation_fee', 500.00))
        cabin_number = request.POST.get('cabin_number', 'Room 101').strip()
        bio = request.POST.get('bio', '').strip()

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/doctor_register.html', {'hospitals': hospitals, 'specialties': specialties})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'auth/doctor_register.html', {'hospitals': hospitals, 'specialties': specialties})

        try:
            hosp = Hospital.objects.get(pk=hospital_id)
            spec = Specialty.objects.get(pk=specialty_id)
        except (Hospital.DoesNotExist, Specialty.DoesNotExist):
            messages.error(request, "Please select a valid hospital and specialty.")
            return render(request, 'auth/doctor_register.html', {'hospitals': hospitals, 'specialties': specialties})

        with transaction.atomic():
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            UserProfile.objects.create(
                user=user, role='DOCTOR', hospital=hosp, phone=phone
            )
            Doctor.objects.create(
                user=user,
                hospital=hosp,
                specialty=spec,
                qualification=qualification,
                experience_years=experience_years,
                consultation_fee=consultation_fee,
                cabin_number=cabin_number,
                slot_duration_minutes=15,
                start_time=time(9, 0),
                end_time=time(17, 0),
                lunch_start=time(13, 0),
                lunch_end=time(14, 0),
                bio=bio
            )
            HospitalDepartment.objects.get_or_create(hospital=hosp, specialty=spec)

        login(request, user)
        messages.success(request, f"Welcome to CarePoint, Dr. {user.get_full_name() or user.username}!")
        return redirect('doctor_portal')

    return render(request, 'auth/doctor_register.html', {
        'hospitals': hospitals,
        'specialties': specialties
    })


# 4. Patient Portal Login & Register
def patient_login_view(request):
    if request.user.is_authenticated:
        return redirect('patient_portal')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('patient_portal')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'auth/patient_login.html')


def patient_register_view(request):
    if request.user.is_authenticated:
        return redirect('patient_portal')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', 'M')
        dob = request.POST.get('date_of_birth') or None
        blood_group = request.POST.get('blood_group', '').strip()

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/patient_register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'auth/patient_register.html')

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        UserProfile.objects.create(
            user=user, role='PATIENT', phone=phone,
            gender=gender, date_of_birth=dob, blood_group=blood_group
        )
        login(request, user)
        messages.success(request, "Patient registration successful! Welcome to your Patient Portal.")
        return redirect('patient_portal')

    return render(request, 'auth/patient_register.html')


# ----------------- Public Views -----------------

def home(request):
    hospitals = Hospital.objects.all().prefetch_related('departments__specialty')[:6]
    specialties = Specialty.objects.all()[:8]
    featured_doctors = Doctor.objects.filter(is_available=True).select_related('hospital', 'specialty', 'user')[:6]
    stats = {
        'total_hospitals': Hospital.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_specialties': Specialty.objects.count(),
        'total_appointments': Appointment.objects.count(),
    }
    return render(request, 'home.html', {
        'hospitals': hospitals,
        'specialties': specialties,
        'featured_doctors': featured_doctors,
        'stats': stats,
    })


def hospital_list(request):
    """Requirement 1: Hospital list with various specialties"""
    specialties = Specialty.objects.all()
    selected_specialty = request.GET.get('specialty')
    search_query = request.GET.get('q', '').strip()
    city_filter = request.GET.get('city', '').strip()

    hospitals = Hospital.objects.all().prefetch_related('departments__specialty', 'doctors')

    if selected_specialty:
        hospitals = hospitals.filter(departments__specialty__code=selected_specialty).distinct()

    if search_query:
        hospitals = hospitals.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

    if city_filter:
        hospitals = hospitals.filter(city__iexact=city_filter)

    cities = Hospital.objects.values_list('city', flat=True).distinct()

    return render(request, 'hospitals.html', {
        'hospitals': hospitals,
        'specialties': specialties,
        'selected_specialty': selected_specialty,
        'search_query': search_query,
        'city_filter': city_filter,
        'cities': cities,
    })


def hospital_detail(request, slug):
    """Requirement 2: Individual departments and doctors for each hospital"""
    hospital = get_object_or_404(Hospital, slug=slug)
    departments = hospital.departments.select_related('specialty').all()
    doctors = hospital.doctors.select_related('specialty', 'user').filter(is_available=True)

    dept_doctors_map = {}
    for dept in departments:
        dept_doctors_map[dept] = doctors.filter(specialty=dept.specialty)

    return render(request, 'hospital_detail.html', {
        'hospital': hospital,
        'departments': departments,
        'dept_doctors_map': dept_doctors_map,
        'total_doctors': doctors.count(),
    })


def doctor_detail(request, doctor_id):
    doctor = get_object_or_404(Doctor.objects.select_related('hospital', 'specialty', 'user'), pk=doctor_id)
    today = date.today()
    slots = doctor.generate_slots_for_date(today)
    return render(request, 'doctor_detail.html', {
        'doctor': doctor,
        'today': today,
        'slots': slots,
    })


# ----------------- 15-Minute Slot & Booking System -----------------

def api_available_slots(request):
    """
    Requirement 3 & 4:
    - Schedules each appointment for 15 minutes
    - Avoids slot booking if already booked
    Returns JSON slots with is_booked status.
    """
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Doctor and Date are required'}, status=400)

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid doctor or date format'}, status=400)

    slots = doctor.generate_slots_for_date(target_date)
    return JsonResponse({
        'doctor_name': str(doctor),
        'date': date_str,
        'slot_duration_minutes': doctor.slot_duration_minutes,
        'slots': slots,
    })


@login_required
def book_appointment(request):
    """
    Requirement 3, 4, 6:
    - 15-minute slot allocation
    - Strict avoidance of double-booking
    - Token generation for each booking
    """
    doctor_id = request.GET.get('doctor') or request.POST.get('doctor')
    initial_doctor = None
    if doctor_id:
        try:
            initial_doctor = Doctor.objects.select_related('hospital', 'specialty', 'user').get(pk=doctor_id)
        except Doctor.DoesNotExist:
            pass

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        date_str = request.POST.get('appointment_date')
        time_slot_str = request.POST.get('time_slot')
        patient_name = request.POST.get('patient_name', '').strip()
        patient_phone = request.POST.get('patient_phone', '').strip()
        patient_age = request.POST.get('patient_age', 30)
        patient_gender = request.POST.get('patient_gender', 'M')
        symptoms = request.POST.get('symptoms', '').strip()
        is_emergency = request.POST.get('is_emergency') == '1'
        emergency_severity = request.POST.get('emergency_severity', 'ROUTINE')

        if not (doctor_id and date_str and time_slot_str and patient_name):
            messages.error(request, "Please fill in all required appointment fields.")
            return redirect(request.path)

        try:
            doctor = Doctor.objects.select_related('hospital', 'specialty').get(pk=doctor_id)
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slot_time = datetime.strptime(time_slot_str, '%H:%M').time()
        except (Doctor.DoesNotExist, ValueError) as e:
            messages.error(request, f"Invalid appointment parameters: {e}")
            return redirect(request.path)

        # End time is strictly +15 minutes
        end_slot_dt = datetime.combine(target_date, slot_time) + timedelta(minutes=15)
        end_time_slot = end_slot_dt.time()

        with transaction.atomic():
            # Check if slot is already booked (Requirement 3: Avoid slot booking if already booked)
            existing_appt = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=target_date,
                time_slot=slot_time,
                status__in=['CONFIRMED', 'EMERGENCY_PRIORITY', 'IN_CONSULTATION']
            ).first()

            if existing_appt:
                if is_emergency:
                    # Emergency swap logic triggered directly on booking (Requirement 5)
                    # Displace existing appointment to next available slot
                    return handle_emergency_preemption(
                        request, doctor, target_date, slot_time, end_time_slot,
                        existing_appt, patient_name, patient_phone, patient_age,
                        patient_gender, symptoms, emergency_severity
                    )
                else:
                    messages.error(
                        request,
                        f"Slot {slot_time.strftime('%I:%M %p')} is already booked! "
                        f"Please select another available 15-minute slot."
                    )
                    return render(request, 'book_appointment.html', {
                        'doctors': Doctor.objects.filter(is_available=True).select_related('hospital', 'specialty'),
                        'selected_doctor': doctor,
                        'selected_date': date_str,
                    })

            # Generate Token Number & Token Code (Requirement 6)
            token_number, token_code = Appointment.generate_token(doctor, target_date)

            status = 'EMERGENCY_PRIORITY' if is_emergency else 'CONFIRMED'
            appointment = Appointment.objects.create(
                token_number=token_number,
                token_code=token_code,
                doctor=doctor,
                patient=request.user,
                patient_name=patient_name,
                patient_phone=patient_phone,
                patient_age=int(patient_age),
                patient_gender=patient_gender,
                appointment_date=target_date,
                time_slot=slot_time,
                end_time_slot=end_time_slot,
                status=status,
                is_emergency=is_emergency,
                emergency_severity=emergency_severity,
                symptoms_summary=symptoms,
            )

        messages.success(
            request,
            f"Appointment confirmed! Your Token Number is #{appointment.token_number} ({appointment.token_code})."
        )
        return redirect('token_card', appointment_id=appointment.id)

    doctors = Doctor.objects.filter(is_available=True).select_related('hospital', 'specialty', 'user')
    hospitals = Hospital.objects.all()
    today_str = date.today().strftime('%Y-%m-%d')
    return render(request, 'book_appointment.html', {
        'doctors': doctors,
        'hospitals': hospitals,
        'selected_doctor': initial_doctor,
        'today_str': today_str,
    })


def handle_emergency_preemption(request, doctor, target_date, slot_time, end_time_slot,
                               displaced_appt, patient_name, patient_phone, patient_age,
                               patient_gender, symptoms, emergency_severity):
    """
    Requirement 5: Swap appointment if there are any emergency cases.
    Automatically moves the routine patient to the next available 15-min slot and
    gives the urgent slot to the emergency patient.
    """
    # Find next available 15-min slot for doctor
    all_slots = doctor.generate_slots_for_date(target_date)
    next_avail_slot = None
    for s in all_slots:
        if not s['is_booked']:
            next_avail_slot = s
            break

    orig_slot_time = displaced_appt.time_slot
    rescheduled_slot_time = next_avail_slot['start_time'] if next_avail_slot else (
        datetime.combine(target_date, displaced_appt.time_slot) + timedelta(minutes=30)
    ).time()

    # Displace existing appointment
    displaced_appt.time_slot = rescheduled_slot_time
    displaced_appt.end_time_slot = (
        datetime.combine(target_date, rescheduled_slot_time) + timedelta(minutes=15)
    ).time()
    displaced_appt.status = 'SWAPPED'
    displaced_appt.save()

    # Create emergency appointment in the requested slot
    token_num, token_code = Appointment.generate_token(doctor, target_date)
    emergency_appt = Appointment.objects.create(
        token_number=token_num,
        token_code=token_code,
        doctor=doctor,
        patient=request.user,
        patient_name=patient_name,
        patient_phone=patient_phone,
        patient_age=int(patient_age),
        patient_gender=patient_gender,
        appointment_date=target_date,
        time_slot=slot_time,
        end_time_slot=end_time_slot,
        status='EMERGENCY_PRIORITY',
        is_emergency=True,
        emergency_severity=emergency_severity,
        symptoms_summary=symptoms,
        emergency_reason=f"Emergency case displaced Token #{displaced_appt.token_number}",
    )

    # Log the swap in EmergencySwapLog
    EmergencySwapLog.objects.create(
        hospital=doctor.hospital,
        doctor=doctor,
        emergency_appointment=emergency_appt,
        displaced_appointment=displaced_appt,
        original_slot_time=orig_slot_time,
        rescheduled_slot_time=rescheduled_slot_time,
        reason=f"Immediate triage for {emergency_severity} emergency case: {patient_name}",
        swapped_by=request.user,
    )

    messages.warning(
        request,
        f"EMERGENCY SWAP EXECUTED: Priority slot allocated ({slot_time.strftime('%I:%M %p')}). "
        f"Displaced patient rescheduled to {rescheduled_slot_time.strftime('%I:%M %p')}."
    )
    return redirect('token_card', appointment_id=emergency_appt.id)


# ----------------- Token Number View (Requirement 6) -----------------

@login_required
def token_card(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor__hospital', 'doctor__specialty', 'doctor__user', 'patient'),
        pk=appointment_id
    )
    # Check current serving token for the doctor today
    active_now = Appointment.objects.filter(
        doctor=appointment.doctor,
        appointment_date=appointment.appointment_date,
        status='IN_CONSULTATION'
    ).first()
    
    current_token_serving = active_now.token_number if active_now else 1
    tokens_ahead = max(0, appointment.token_number - current_token_serving)
    est_wait_minutes = tokens_ahead * 15

    return render(request, 'token_card.html', {
        'appointment': appointment,
        'current_token_serving': current_token_serving,
        'tokens_ahead': tokens_ahead,
        'est_wait_minutes': est_wait_minutes,
    })


# ----------------- Emergency Swap View (Requirement 5) -----------------

@login_required
@role_required(['ADMIN', 'HOSPITAL_ADMIN', 'DOCTOR'])
def manual_emergency_swap(request):
    """
    Requirement 5: Dedicated tool to swap appointment slots when an emergency arrives.
    Doctors and Hospital Admins can swap any booked slot with an emergency patient.
    """
    if request.method == 'POST':
        appt_a_id = request.POST.get('target_appointment_id')
        emergency_name = request.POST.get('emergency_patient_name')
        emergency_phone = request.POST.get('emergency_patient_phone')
        emergency_age = request.POST.get('emergency_patient_age', 35)
        emergency_gender = request.POST.get('emergency_gender', 'M')
        emergency_reason = request.POST.get('reason', 'Critical condition arrived at triage')

        target_appt = get_object_or_404(Appointment, pk=appt_a_id)
        doctor = target_appt.doctor

        with transaction.atomic():
            # Find next free slot on the same day for displaced patient
            all_slots = doctor.generate_slots_for_date(target_appt.appointment_date)
            next_free = next((s for s in all_slots if not s['is_booked']), None)

            orig_time = target_appt.time_slot
            if next_free:
                new_time = next_free['start_time']
                new_end = next_free['end_time']
            else:
                new_time = (datetime.combine(target_appt.appointment_date, orig_time) + timedelta(minutes=45)).time()
                new_end = (datetime.combine(target_appt.appointment_date, new_time) + timedelta(minutes=15)).time()

            # Displace target appointment
            target_appt.time_slot = new_time
            target_appt.end_time_slot = new_end
            target_appt.status = 'SWAPPED'
            target_appt.save()

            # Create emergency appointment in the target slot
            token_num, token_code = Appointment.generate_token(doctor, target_appt.appointment_date)
            emergency_appt = Appointment.objects.create(
                token_number=token_num,
                token_code=token_code,
                doctor=doctor,
                patient=request.user,
                patient_name=emergency_name,
                patient_phone=emergency_phone,
                patient_age=int(emergency_age),
                patient_gender=emergency_gender,
                appointment_date=target_appt.appointment_date,
                time_slot=orig_time,
                end_time_slot=(datetime.combine(target_appt.appointment_date, orig_time) + timedelta(minutes=15)).time(),
                status='EMERGENCY_PRIORITY',
                is_emergency=True,
                emergency_severity='CRITICAL_EMERGENCY',
                emergency_reason=emergency_reason,
            )

            # Record in Swap Log
            EmergencySwapLog.objects.create(
                hospital=doctor.hospital,
                doctor=doctor,
                emergency_appointment=emergency_appt,
                displaced_appointment=target_appt,
                original_slot_time=orig_time,
                rescheduled_slot_time=new_time,
                reason=emergency_reason,
                swapped_by=request.user,
            )

        messages.success(
            request,
            f"Emergency Swap Completed! Emergency patient assigned to {orig_time.strftime('%I:%M %p')}. "
            f"Displaced patient (Token #{target_appt.token_number}) rescheduled to {new_time.strftime('%I:%M %p')}."
        )
        return redirect('dashboard_redirect')

    return redirect('dashboard_redirect')


# ----------------- Health Meters View (Requirement 7) -----------------

def health_meters(request):
    """
    Requirement 7:
    Visual and interactive meters of:
    1. Sugar Meter (Fasting & Postprandial)
    2. Cholesterol Meter (Total, HDL, LDL, Triglycerides)
    3. Overweight / Underweight Meter (BMI Gauge)
    4. Pulse Rate Meter (BPM Heart Rate)
    """
    past_vitals = None
    if request.user.is_authenticated:
        past_vitals = PatientVital.objects.filter(patient=request.user)[:5]

    if request.method == 'POST' and request.user.is_authenticated:
        sugar_fasting = request.POST.get('sugar_fasting') or None
        sugar_pp = request.POST.get('sugar_postprandial') or None
        cholesterol_total = request.POST.get('cholesterol_total') or None
        cholesterol_hdl = request.POST.get('cholesterol_hdl') or None
        cholesterol_ldl = request.POST.get('cholesterol_ldl') or None
        triglycerides = request.POST.get('triglycerides') or None
        weight_kg = request.POST.get('weight_kg') or None
        height_cm = request.POST.get('height_cm') or None
        pulse_rate = request.POST.get('pulse_rate') or None
        notes = request.POST.get('notes', '').strip()

        vital = PatientVital(
            patient=request.user,
            sugar_fasting=sugar_fasting,
            sugar_postprandial=sugar_pp,
            cholesterol_total=cholesterol_total,
            cholesterol_hdl=cholesterol_hdl,
            cholesterol_ldl=cholesterol_ldl,
            triglycerides=triglycerides,
            weight_kg=weight_kg,
            height_cm=height_cm,
            pulse_rate=pulse_rate,
            notes=notes,
        )
        vital.calculate_metrics()
        vital.save()
        messages.success(request, "Your health vitals and meter readings have been saved!")
        return redirect('health_meters')

    return render(request, 'health_meters.html', {
        'past_vitals': past_vitals,
    })


# ----------------- Symptom Checker -----------------

def symptom_checker(request):
    """
    Comprehensive interactive Symptom Checker.
    Evaluates symptoms, computes risk level, identifies emergency red flags,
    and recommends matching medical specialties and doctors with 15-minute slot booking.
    """
    specialties = Specialty.objects.all()
    hospitals = Hospital.objects.all()

    if request.method == 'POST':
        selected_symptoms = request.POST.getlist('symptoms')
        severity = request.POST.get('severity', 'MODERATE')
        duration = request.POST.get('duration', '1-3 days')
        patient_age = request.POST.get('patient_age', 30)

        # Triage Evaluation Algorithm
        emergency_keywords = [
            'chest_pain', 'shortness_of_breath', 'severe_chest_pressure',
            'facial_droop', 'speech_difficulty', 'unconscious', 'severe_head_trauma'
        ]
        has_emergency = any(s in selected_symptoms for s in emergency_keywords) or severity == 'SEVERE'

        risk_level = 'CRITICAL_EMERGENCY' if has_emergency else ('HIGH' if severity == 'SEVERE' else 'MODERATE')

        # Map to Medical Specialty
        rec_specialty_code = 'GMED'
        if any(s in ['chest_pain', 'palpitations', 'high_blood_pressure', 'shortness_of_breath'] for s in selected_symptoms):
            rec_specialty_code = 'CARD'
        elif any(s in ['headache', 'dizziness', 'seizure', 'numbness', 'memory_loss'] for s in selected_symptoms):
            rec_specialty_code = 'NEUR'
        elif any(s in ['joint_pain', 'fracture', 'back_pain', 'swollen_joints'] for s in selected_symptoms):
            rec_specialty_code = 'ORTH'
        elif any(s in ['rash', 'itching', 'skin_lesion', 'hair_loss'] for s in selected_symptoms):
            rec_specialty_code = 'DERM'
        elif any(s in ['abdominal_pain', 'vomiting', 'diarrhea', 'acid_reflux'] for s in selected_symptoms):
            rec_specialty_code = 'GAST'
        elif any(s in ['ear_pain', 'hearing_loss', 'sore_throat', 'sinus_congestion'] for s in selected_symptoms):
            rec_specialty_code = 'ENT'

        try:
            recommended_specialty = Specialty.objects.get(code=rec_specialty_code)
        except Specialty.DoesNotExist:
            recommended_specialty = Specialty.objects.first()

        recommended_doctors = Doctor.objects.filter(
            specialty=recommended_specialty, is_available=True
        ).select_related('hospital')[:4]

        # Save record if user logged in
        check_record = None
        if request.user.is_authenticated:
            check_record = SymptomCheckRecord.objects.create(
                patient=request.user,
                symptoms=selected_symptoms,
                severity=severity,
                duration=duration,
                risk_level=risk_level,
                recommended_specialty=recommended_specialty,
                is_emergency=has_emergency,
                triage_summary=f"Evaluated {len(selected_symptoms)} symptoms. Risk: {risk_level}.",
                recommended_action="Immediate Hospital ER visit" if has_emergency else f"Consult {recommended_specialty.name} specialist within 24-48 hours."
            )

        return render(request, 'symptom_checker_result.html', {
            'selected_symptoms': selected_symptoms,
            'severity': severity,
            'duration': duration,
            'risk_level': risk_level,
            'is_emergency': has_emergency,
            'recommended_specialty': recommended_specialty,
            'recommended_doctors': recommended_doctors,
            'check_record': check_record,
        })

    return render(request, 'symptom_checker.html', {
        'specialties': specialties,
        'hospitals': hospitals,
    })


# ----------------- 4 Separate Portals -----------------

# 1. ADMIN PORTAL
@login_required
@role_required(['ADMIN'])
def admin_portal(request):
    hospitals = Hospital.objects.all().prefetch_related('doctors', 'departments')
    doctors = Doctor.objects.all().select_related('hospital', 'specialty', 'user')
    specialties = Specialty.objects.all()
    appointments = Appointment.objects.all().select_related('doctor__hospital', 'doctor__specialty', 'patient').order_by('-appointment_date', '-time_slot')[:20]
    swap_logs = EmergencySwapLog.objects.all().select_related('hospital', 'doctor', 'emergency_appointment', 'displaced_appointment', 'swapped_by')[:10]

    stats = {
        'total_hospitals': hospitals.count(),
        'total_doctors': doctors.count(),
        'total_appointments': Appointment.objects.count(),
        'emergency_appointments': Appointment.objects.filter(is_emergency=True).count(),
        'total_swaps': EmergencySwapLog.objects.count(),
        'total_patients': UserProfile.objects.filter(role='PATIENT').count(),
    }

    return render(request, 'portals/admin_portal.html', {
        'hospitals': hospitals,
        'doctors': doctors,
        'specialties': specialties,
        'appointments': appointments,
        'swap_logs': swap_logs,
        'stats': stats,
    })


# 2. HOSPITAL PORTAL
@login_required
@role_required(['ADMIN', 'HOSPITAL_ADMIN'])
def hospital_portal(request):
    profile = getattr(request.user, 'profile', None)
    # Determine which hospital: admin's assigned hospital or first hospital
    hospital = profile.hospital if (profile and profile.hospital) else Hospital.objects.first()

    today = date.today()
    departments = hospital.departments.select_related('specialty').all()
    doctors = hospital.doctors.select_related('specialty', 'user').all()
    today_appointments = Appointment.objects.filter(
        doctor__hospital=hospital,
        appointment_date=today
    ).select_related('doctor', 'doctor__specialty', 'patient').order_by('time_slot')

    emergency_queue = today_appointments.filter(is_emergency=True)
    swap_logs = EmergencySwapLog.objects.filter(hospital=hospital).select_related('doctor', 'emergency_appointment', 'displaced_appointment')[:10]

    # Handle Add Doctor or Add Department from Hospital Portal
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_department':
            spec_id = request.POST.get('specialty_id')
            floor = request.POST.get('floor', '1st Floor')
            head = request.POST.get('head_of_department', '')
            opd = request.POST.get('opd_rooms', 'OPD 101')
            spec = get_object_or_404(Specialty, pk=spec_id)
            HospitalDepartment.objects.get_or_create(
                hospital=hospital, specialty=spec,
                defaults={'floor': floor, 'head_of_department': head, 'opd_rooms': opd}
            )
            messages.success(request, f"Department of {spec.name} added to {hospital.name}.")
            return redirect('hospital_portal')

    return render(request, 'portals/hospital_portal.html', {
        'hospital': hospital,
        'all_hospitals': Hospital.objects.all(),
        'departments': departments,
        'doctors': doctors,
        'today': today,
        'today_appointments': today_appointments,
        'emergency_queue': emergency_queue,
        'swap_logs': swap_logs,
        'all_specialties': Specialty.objects.all(),
    })


# 3. DOCTOR PORTAL
@login_required
@role_required(['ADMIN', 'DOCTOR'])
def doctor_portal(request):
    doctor = getattr(request.user, 'doctor_profile', None)
    if not doctor:
        # Fallback if admin viewing doctor portal
        doctor = Doctor.objects.first()

    today = date.today()
    selected_date_str = request.GET.get('date')
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else today

    slots = doctor.generate_slots_for_date(selected_date)
    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=selected_date
    ).select_related('patient').order_by('time_slot')

    # Current Serving token
    active_appt = appointments.filter(status='IN_CONSULTATION').first()
    next_appt = appointments.filter(status__in=['CONFIRMED', 'EMERGENCY_PRIORITY']).first()

    # Patient Vitals for appointments
    recent_patient_vitals = PatientVital.objects.filter(
        patient__appointments__doctor=doctor
    ).distinct().order_by('-recorded_at')[:5]

    return render(request, 'portals/doctor_portal.html', {
        'doctor': doctor,
        'selected_date': selected_date,
        'slots': slots,
        'appointments': appointments,
        'active_appt': active_appt,
        'next_appt': next_appt,
        'recent_patient_vitals': recent_patient_vitals,
        'today_str': today.strftime('%Y-%m-%d'),
    })


@login_required
@role_required(['ADMIN', 'DOCTOR'])
def update_appointment_status(request, appointment_id):
    """Doctor actions: Call Next Token, Start Consultation, Mark Completed"""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    new_status = request.POST.get('status')
    notes = request.POST.get('doctor_notes', '')
    prescription = request.POST.get('prescription', '')

    if new_status in dict(Appointment.STATUS_CHOICES):
        appointment.status = new_status
        if notes:
            appointment.doctor_notes = notes
        if prescription:
            appointment.prescription = prescription
        appointment.save()
        messages.success(request, f"Appointment Token #{appointment.token_number} updated to {appointment.get_status_display()}.")

    return redirect('doctor_portal')


# 4. PATIENT PORTAL
@login_required
@role_required(['ADMIN', 'PATIENT'])
def patient_portal(request):
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('doctor__hospital', 'doctor__specialty').order_by('-appointment_date', '-time_slot')

    vitals = PatientVital.objects.filter(patient=request.user).order_by('-recorded_at')
    latest_vital = vitals.first()
    symptom_checks = SymptomCheckRecord.objects.filter(patient=request.user).order_by('-created_at')[:5]

    return render(request, 'portals/patient_portal.html', {
        'appointments': appointments,
        'vitals': vitals,
        'latest_vital': latest_vital,
        'symptom_checks': symptom_checks,
    })


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)
    if appointment.status in ['CONFIRMED', 'EMERGENCY_PRIORITY']:
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, f"Appointment Token #{appointment.token_number} has been cancelled.")
    else:
        messages.error(request, "This appointment cannot be cancelled.")
    return redirect('patient_portal')
