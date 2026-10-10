def auth_context(request):
    """Provides current user profile and role to all templates."""
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        role = profile.role if profile else ('ADMIN' if request.user.is_superuser else 'PATIENT')
        return {
            'user_profile': profile,
            'user_role': role,
            'is_admin': role == 'ADMIN' or request.user.is_superuser,
            'is_hospital_admin': role == 'HOSPITAL_ADMIN',
            'is_doctor': role == 'DOCTOR',
            'is_patient': role == 'PATIENT',
        }
    return {
        'user_profile': None,
        'user_role': None,
        'is_admin': False,
        'is_hospital_admin': False,
        'is_doctor': False,
        'is_patient': False,
    }
