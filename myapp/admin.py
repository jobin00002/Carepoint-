from django.contrib import admin
from .models import (
    UserProfile, Specialty, Hospital, HospitalDepartment, Doctor,
    Appointment, EmergencySwapLog, PatientVital, SymptomCheckRecord
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'hospital')
    list_filter = ('role', 'gender', 'hospital')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'icon')
    search_fields = ('name', 'code')

@admin.register(Hospital)
class HospitalAdminSite(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'emergency_helpline', 'rating', 'total_beds')
    search_fields = ('name', 'city')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(HospitalDepartment)
class HospitalDepartmentAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'specialty', 'floor', 'head_of_department', 'opd_rooms')
    list_filter = ('hospital', 'specialty')

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'hospital', 'specialty', 'qualification', 'consultation_fee', 'cabin_number', 'is_available')
    list_filter = ('hospital', 'specialty', 'is_available')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'cabin_number')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('token_code', 'token_number', 'patient_name', 'doctor', 'appointment_date', 'time_slot', 'status', 'is_emergency')
    list_filter = ('status', 'is_emergency', 'appointment_date', 'doctor__hospital', 'doctor__specialty')
    search_fields = ('token_code', 'patient_name', 'patient_phone')

@admin.register(EmergencySwapLog)
class EmergencySwapLogAdmin(admin.ModelAdmin):
    list_display = ('swapped_at', 'hospital', 'doctor', 'emergency_appointment', 'displaced_appointment', 'swapped_by')
    list_filter = ('hospital', 'doctor')

@admin.register(PatientVital)
class PatientVitalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'sugar_status', 'cholesterol_status', 'weight_status', 'pulse_status', 'recorded_at')
    list_filter = ('sugar_status', 'cholesterol_status', 'weight_status', 'pulse_status')

@admin.register(SymptomCheckRecord)
class SymptomCheckRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'risk_level', 'recommended_specialty', 'is_emergency', 'created_at')
    list_filter = ('risk_level', 'is_emergency', 'recommended_specialty')
