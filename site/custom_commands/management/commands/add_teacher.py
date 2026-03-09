import secrets
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from judge.models import Organization, Profile


class Command(BaseCommand):
    help = 'Create a teacher account (staff user with organization admin)'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Login username')
        parser.add_argument('--password', default='', help='Password (auto-generated if omitted)')
        parser.add_argument('--email', default='', help='Email address')
        parser.add_argument('--first-name', default='', help='First name')
        parser.add_argument('--last-name', default='', help='Last name')
        parser.add_argument('--organization', default='', help='Organization slug to join as admin')

    def handle(self, *args, **options):
        username = options['username']

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'User already exists: {username}')
            return

        password = options['password']
        generated = False
        if not password:
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
            generated = True

        user = User.objects.create_user(
            username=username,
            password=password,
            email=options['email'],
            first_name=options['first_name'],
            last_name=options['last_name'],
            is_staff=True,
        )

        profile, _ = Profile.objects.get_or_create(user=user)

        org_slug = options['organization']
        if org_slug:
            try:
                org = Organization.objects.get(slug=org_slug)
                org.members.add(profile)
                org.admins.add(profile)
            except Organization.DoesNotExist:
                self.stderr.write(f'Warning: organization "{org_slug}" not found, user created without organization')

        self.stdout.write(f'Created teacher: {username}')
        self.stdout.write(f'Password: {password}' + (' (auto-generated)' if generated else ''))
