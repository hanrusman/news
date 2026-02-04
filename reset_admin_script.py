from django.contrib.auth import get_user_model
User = get_user_model()
try:
    u, created = User.objects.get_or_create(username='admin')
    u.set_password('admin')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    action = "Created" if created else "Updated"
    print(f"SUCCESS: {action} superuser 'admin' with password 'admin'")
except Exception as e:
    print(f"ERROR: {e}")
