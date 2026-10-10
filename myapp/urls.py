from django.urls import path
from . import views

urlpatterns = [
    # Public & Information
    path('', views.home, name='home'),
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospital/<slug:slug>/', views.hospital_detail, name='hospital_detail'),
    path('doctor/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    
    # 15-Min Appointment Booking & Slots
    path('book/', views.book_appointment, name='book_appointment'),
    path('token/<int:appointment_id>/', views.token_card, name='token_card'),
    path('api/slots/', views.api_available_slots, name='api_available_slots'),
    
    # Emergency Swap
    path('emergency-swap/', views.manual_emergency_swap, name='emergency_swap'),
    
    # Health Meters (Sugar, Cholesterol, BMI, Pulse Rate)
    path('health-meters/', views.health_meters, name='health_meters'),
    
    # Symptom Checker
    path('symptom-checker/', views.symptom_checker, name='symptom_checker'),
    
    # Authentication & Portal Navigation
    path('login/', views.portal_select_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.patient_register_view, name='register'),
    path('portal-select/', views.portal_select_view, name='portal_select'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # Dedicated Separate Login & Register Endpoints
    # 1. Admin Portal (Login ONLY - No register page for admin!)
    path('admin-login/', views.admin_login_view, name='admin_login'),
    
    # 2. Hospital Portal (Separate Login & Register)
    path('hospital-login/', views.hospital_login_view, name='hospital_login'),
    path('hospital-register/', views.hospital_register_view, name='hospital_register'),
    
    # 3. Doctor Portal (Separate Login & Register)
    path('doctor-login/', views.doctor_login_view, name='doctor_login'),
    path('doctor-register/', views.doctor_register_view, name='doctor_register'),
    
    # 4. Patient Portal (Separate Login & Register)
    path('patient-login/', views.patient_login_view, name='patient_login'),
    path('patient-register/', views.patient_register_view, name='patient_register'),
    
    # Separate 4 Portals
    path('admin-portal/', views.admin_portal, name='admin_portal'),
    path('hospital-portal/', views.hospital_portal, name='hospital_portal'),
    path('doctor-portal/', views.doctor_portal, name='doctor_portal'),
    path('patient-portal/', views.patient_portal, name='patient_portal'),
    
    # Actions
    path('appointment/<int:appointment_id>/status/', views.update_appointment_status, name='update_appointment_status'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
]
