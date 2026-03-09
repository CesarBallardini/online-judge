"""
R5RS Scheme unit-test grader for DMOJ.

Replaces the student submission with a Racket wrapper that:
  1. Creates an R5RS sandbox (racket/sandbox)
  2. Loads student definitions into the sandbox
  3. Runs teacher-written unit tests (tests.rkt)
  4. Outputs structured RESULT lines

The grader runs the wrapper once, caches per-test verdicts,
and returns them as DMOJ calls grade() for each test case.

Deploy into each problem directory as ``grader.py`` via:
    ./manage.sh deploy-scheme-problem <problem-code>
"""

from dmoj.graders import StandardGrader
from dmoj.result import Result

# Racket code appended after the preamble that defines student-source / tests-source.
_WRAPPER_BODY = r'''
;; ---- #lang check ------------------------------------------------------------
(define (strip-lang src)
  (define lines (string-split src "\n"))
  (cond
    [(null? lines) (values src #t)]
    [else
     (define first (string-trim (car lines)))
     (cond
       [(regexp-match? #rx"^#lang\\s+r5rs" first)
        (values (string-join (cdr lines) "\n") #t)]
       [(regexp-match? #rx"^#lang" first)
        (values src #f)]
       [else (values src #t)])]))

(define-values (cleaned-source r5rs-ok?) (strip-lang student-source))

;; ---- Parse test definitions --------------------------------------------------
(define tests
  (with-input-from-string tests-source
    (lambda ()
      (let loop ([acc '()])
        (define f (read))
        (if (eof-object? f) (reverse acc) (loop (cons f acc)))))))

(define test-count (length tests))

;; ---- Non-R5RS rejection ------------------------------------------------------
(unless r5rs-ok?
  (for ([i (in-range test-count)])
    (displayln "RESULT:NON_R5RS"))
  (exit 0))

;; ---- Create R5RS sandbox -----------------------------------------------------
(sandbox-memory-limit 128)        ; MB
(sandbox-eval-limits '(5 128))    ; 5 s / 128 MB per expression
(sandbox-path-permissions '())

(define sandbox-eval
  (with-handlers ([exn:fail? (lambda (ex)
    (define msg (regexp-replace* #rx"[\r\n]" (exn-message ex) " "))
    (for ([i (in-range test-count)])
      (printf "RESULT:COMPILATION_ERROR|error|~a\n" msg))
    (exit 0))])
    (make-evaluator 'r5rs #:allow-for-require '() cleaned-source)))

;; ---- Run tests ---------------------------------------------------------------
(for ([t (in-list tests)])
  (match t
    [(list 'test name expr expected)
     (define expects-error? (eq? expected 'error))
     (with-handlers
       ([exn:fail:resource? (lambda (ex)
          (define msg (regexp-replace* #rx"[\r\n]" (exn-message ex) " "))
          (printf "RESULT:FAIL|~a|resource limit: ~a\n" name msg))]
        [exn:fail? (lambda (ex)
          (define msg (regexp-replace* #rx"[\r\n]" (exn-message ex) " "))
          (if expects-error?
              (printf "RESULT:PASS|~a\n" name)
              (printf "RESULT:FAIL|~a|exception: ~a\n" name msg)))])
       (if expects-error?
           ;; Expression must raise an error to pass
           (let ([result (sandbox-eval expr)])
             (printf "RESULT:FAIL|~a|expected error but got ~s\n" name result))
           ;; Expression must return expected value
           (let* ([result   (sandbox-eval expr)]
                  [exp-val  (sandbox-eval expected)]
                  [pass?    (equal? result exp-val)])
             (if pass?
                 (printf "RESULT:PASS|~a\n" name)
                 (printf "RESULT:FAIL|~a|expected ~s got ~s\n"
                         name exp-val result)))))]
    [_ (displayln "RESULT:FAIL|unknown|invalid test form")]))
'''


class Grader(StandardGrader):
    """Custom DMOJ grader that runs R5RS unit tests on student submissions."""

    def __init__(self, judge, problem, language, source):
        wrapper = Grader._build_wrapper(source, problem)
        super().__init__(judge, problem, language, wrapper)
        self._test_results = None   # dict[int, (status, name, detail)]
        self._process_error = 0     # Result flag for process-level errors

    # ---- wrapper construction -------------------------------------------------

    @staticmethod
    def _racket_escape(s):
        """Escape a Python string for embedding inside a Racket string literal."""
        return (s
                .replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t')
                .replace('\0', '\\0'))

    @staticmethod
    def _build_wrapper(source, problem):
        """Generate the full ``#lang racket`` wrapper source."""
        student = source.decode('utf-8', errors='replace')
        tests = problem.problem_data['tests.rkt'].decode('utf-8')

        preamble = (
            '#lang racket\n\n'
            '(require racket/sandbox)\n\n'
            '(define student-source "' + Grader._racket_escape(student) + '")\n'
            '(define tests-source "' + Grader._racket_escape(tests) + '")\n'
        )
        return (preamble + _WRAPPER_BODY).encode('utf-8')

    # ---- grading --------------------------------------------------------------

    def _run_all_tests(self, case):
        """Launch the wrapper once and parse every RESULT line."""
        self._current_proc = self.binary.launch(
            time=self.problem.time_limit,
            memory=self.problem.memory_limit,
            pipe_stderr=True,
        )
        output, error = self._current_proc.safe_communicate(b'')

        # Detect process-level TLE / MLE / RTE
        probe = Result(case)
        self.populate_result(error, probe, self._current_proc)

        if probe.result_flag & (Result.TLE | Result.MLE | Result.RTE | Result.IR):
            self._process_error = probe.result_flag
            self._test_results = {}
            return

        # Parse structured RESULT lines (use a separate counter so that
        # non-RESULT lines like Racket warnings don't shift the index).
        self._test_results = {}
        if output:
            result_idx = 0
            for line in output.decode('utf-8', errors='replace').strip().split('\n'):
                line = line.strip()
                if not line.startswith('RESULT:'):
                    continue
                payload = line[len('RESULT:'):]
                parts = payload.split('|', 2)
                status = parts[0]
                name = parts[1] if len(parts) > 1 else ''
                detail = parts[2] if len(parts) > 2 else ''
                self._test_results[result_idx] = (status, name, detail)
                result_idx += 1

    def grade(self, case):
        """Return the cached verdict for *case.position*."""
        if self._test_results is None:
            self._run_all_tests(case)

        result = Result(case)

        # Process-level error -> propagate to every test case
        if self._process_error:
            result.result_flag = self._process_error
            result.points = 0
            return result

        idx = case.position
        if idx not in self._test_results:
            result.result_flag = Result.IE
            result.points = 0
            result.feedback = 'Test did not produce output'
            return result

        status, name, detail = self._test_results[idx]

        if status == 'PASS':
            result.result_flag = Result.AC
            result.points = case.points
            result.proc_output = name.encode('utf-8')
        elif status == 'NON_R5RS':
            result.result_flag = Result.WA
            result.points = 0
            result.feedback = 'Non-R5RS language detected'
        elif status == 'COMPILATION_ERROR':
            result.result_flag = Result.IR
            result.points = 0
            result.feedback = detail or 'Compilation error'
        else:  # FAIL
            result.result_flag = Result.WA
            result.points = 0
            result.feedback = detail or 'Test failed: {}'.format(name)

        return result
