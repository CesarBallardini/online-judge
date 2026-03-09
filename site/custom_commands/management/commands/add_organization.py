from django.core.management.base import BaseCommand
from judge.models import Organization


class Command(BaseCommand):
    help = 'Create an organization'

    def add_arguments(self, parser):
        parser.add_argument('--name', required=True, help='Display name')
        parser.add_argument('--slug', required=True, help='URL slug (lowercase, no spaces)')
        parser.add_argument('--short-name', default='', help='Short name / abbreviation')

    def handle(self, *args, **options):
        slug = options['slug']
        name = options['name']
        short_name = options['short_name'] or name

        if Organization.objects.filter(slug=slug).exists():
            self.stdout.write(f'Organization already exists: {slug}')
            return

        Organization.objects.create(
            slug=slug,
            name=name,
            short_name=short_name,
        )
        self.stdout.write(f'Created organization: {name} ({slug})')
