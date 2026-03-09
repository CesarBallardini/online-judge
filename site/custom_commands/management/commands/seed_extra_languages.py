from django.core.management.base import BaseCommand
from judge.models import Language


EXTRA_LANGUAGES = [
    {
        'key': 'PRO',
        'name': 'Prolog',
        'common_name': 'Prolog',
        'ace': 'prolog',
        'pygments': 'prolog',
        'extension': 'pl',
    },
    {
        'key': 'RKT',
        'name': 'Racket',
        'common_name': 'Racket',
        'ace': 'scheme',
        'pygments': 'racket',
        'extension': 'rkt',
    },
]


class Command(BaseCommand):
    help = 'Seed extra judge languages (Prolog, Racket) not in upstream language_small fixture'

    def handle(self, *args, **options):
        for lang in EXTRA_LANGUAGES:
            key = lang.pop('key')
            obj, created = Language.objects.get_or_create(key=key, defaults=lang)
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  {key}: {status}')
