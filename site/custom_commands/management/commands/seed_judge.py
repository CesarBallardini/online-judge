import os

from django.core.management.base import BaseCommand
from judge.models import Judge


class Command(BaseCommand):
    help = 'Register the judge in the database using JUDGE_NAME and JUDGE_KEY env vars'

    def handle(self, *args, **options):
        name = os.environ.get('JUDGE_NAME', '').strip()
        key = os.environ.get('JUDGE_KEY', '').strip()

        if not name or not key:
            self.stderr.write('JUDGE_NAME or JUDGE_KEY not set, skipping judge registration')
            return

        obj, created = Judge.objects.get_or_create(
            name=name,
            defaults={'auth_key': key, 'is_blocked': False},
        )
        if created:
            self.stdout.write(f'  Judge "{name}": created')
        else:
            if obj.auth_key != key:
                obj.auth_key = key
                obj.save(update_fields=['auth_key'])
                self.stdout.write(f'  Judge "{name}": updated auth_key')
            else:
                self.stdout.write(f'  Judge "{name}": already exists')
