from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    help = 'Creates or retrieves an API token for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the API token')

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist.'))
            self.stdout.write('Create a user first with: python manage.py createsuperuser')
            return

        token, created = Token.objects.get_or_create(user=user)

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created new API token for user "{username}"'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Retrieved existing API token for user "{username}"'))

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('═' * 60))
        self.stdout.write(self.style.WARNING(f'API Token: {token.key}'))
        self.stdout.write(self.style.WARNING('═' * 60))
        self.stdout.write('')
        self.stdout.write('Add this to your .env file:')
        self.stdout.write(f'N8N_API_TOKEN={token.key}')
        self.stdout.write('')
        self.stdout.write('Use in n8n HTTP Request headers:')
        self.stdout.write(f'Authorization: Token {token.key}')
