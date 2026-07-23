"""
Submit a solution to a problem and wait for the verdict.

Used by './manage.sh verify' to smoke-test the judge pipeline end to end
(site -> bridged -> judge -> grader -> results back).

Usage:
  python manage.py submit_solution --problem max-of-list --language RKT < solution.rkt
"""

import sys
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from judge.judgeapi import judge_submission
from judge.models import Language, Problem, Profile, Submission, SubmissionSource

FINAL_STATUSES = ('D', 'IE', 'CE', 'AB')


class Command(BaseCommand):
    help = 'Submit a solution (from --file or stdin) and wait for the verdict'

    def add_arguments(self, parser):
        parser.add_argument('--problem', required=True, help='Problem code')
        parser.add_argument('--user', default='admin', help='Submitting username (default: admin)')
        parser.add_argument('--language', default='RKT', help='Language key (default: RKT)')
        parser.add_argument('--file', default='-', help='Solution file, "-" for stdin (default)')
        parser.add_argument('--timeout', type=int, default=120, help='Seconds to wait for a verdict')
        parser.add_argument('--expect', default='AC', help='Expected result code (default: AC)')

    def handle(self, *args, **options):
        if options['file'] == '-':
            source = sys.stdin.read()
        else:
            with open(options['file'], encoding='utf-8') as fh:
                source = fh.read()
        if not source.strip():
            raise CommandError('Empty solution source')

        try:
            problem = Problem.objects.get(code=options['problem'])
        except Problem.DoesNotExist:
            raise CommandError(f'Problem not found: {options["problem"]}')
        try:
            language = Language.objects.get(key=options['language'])
        except Language.DoesNotExist:
            raise CommandError(f'Language not found: {options["language"]}')
        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(f'User not found: {options["user"]}')

        profile, _ = Profile.objects.get_or_create(user=user, defaults={'language': language})

        submission = Submission.objects.create(user=profile, problem=problem, language=language)
        SubmissionSource.objects.create(submission=submission, source=source)
        judge_submission(submission)
        self.stdout.write(f'Submission #{submission.id} sent to judge, waiting...')

        deadline = time.monotonic() + options['timeout']
        while time.monotonic() < deadline:
            time.sleep(2)
            submission.refresh_from_db()
            if submission.status in FINAL_STATUSES:
                break
        else:
            raise CommandError(f'Timed out after {options["timeout"]}s (status: {submission.status})')

        for case in submission.test_cases.order_by('case'):
            self.stdout.write(
                f'  case {case.case:>2}: {case.status:<3} {case.points}/{case.total}'
                + (f'  [{case.feedback}]' if case.feedback else '')
            )
        self.stdout.write(
            f'Verdict: {submission.result}  points: {submission.points}/{problem.points}  '
            f'time: {submission.time and round(submission.time, 2)}s'
        )

        if submission.result != options['expect']:
            raise CommandError(f'Expected {options["expect"]}, got {submission.result}')
        self.stdout.write(self.style.SUCCESS(f'OK: got expected result {options["expect"]}'))
