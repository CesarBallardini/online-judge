# Scheme Problems

This folder contains problems designed for Racket (Scheme). There are two problem formats:

1. **Standard (stdin/stdout)** — students write full programs with `(read)` and `(display)`
2. **Unit-test (R5RS)** — students submit pure function definitions, tested via `racket/sandbox`

## Folder Structure

```
scheme-example/
├── README.md
├── max-of-numbers/           # Standard format (stdin/stdout)
│   ├── init.yml
│   ├── solution.rkt
│   ├── 1.in / 1.out
│   └── ...
└── max-of-list/              # Unit-test format (R5RS)
    ├── init.yml              # custom_judge: grader.py
    ├── tests.rkt             # Teacher's unit tests
    └── solution.rkt          # Reference R5RS solution
```

---

## Standard Format (stdin/stdout)

### Deploy

```bash
cp -r scheme-example/max-of-numbers/ data/problems/max-of-numbers/
```

### Create in Django

```bash
./manage.sh create-problem \
  --code max-of-numbers \
  --name "Maximum of a List" \
  --description "Given a list of integers find the maximum" \
  --group Scheme \
  --types "Recursion,Lists,guia_1" \
  --languages RKT
```

### init.yml format

```yaml
test_cases:
  - {in: 1.in, out: 1.out, points: 10}
  - {in: 2.in, out: 2.out, points: 10}
```

---

## Unit-Test Format (R5RS)

Students submit **function definitions only** (no `#lang`, no I/O). A custom grader loads them into an R5RS sandbox and runs teacher-written unit tests.

### How it works

1. Student submits a `.rkt` file with only function definitions
2. DMOJ sees `custom_judge: grader.py` in `init.yml`
3. `grader.py` builds a Racket wrapper that:
   - Strips any `#lang r5rs` line (rejects other `#lang` pragmas)
   - Loads student code into an R5RS sandbox (`make-evaluator 'r5rs`)
   - Runs each test from `tests.rkt`
   - Outputs structured `RESULT:PASS/FAIL` lines
4. The grader parses the output and returns per-test verdicts

### R5RS enforcement

- **`#lang` stripping**: `#lang r5rs` is stripped; any other `#lang` is rejected
- **Sandbox**: `(make-evaluator 'r5rs #:allow-for-require '())` — only R5RS bindings
- **Resource limits**: 5 seconds / 128 MB per expression, no filesystem access

### Deploy

```bash
./manage.sh deploy-scheme-problem max-of-list
```

This copies `init.yml`, `tests.rkt` from `scheme-example/max-of-list/` and the grader from `judge/scheme_grader.py` into `data/problems/max-of-list/`.

### Create in Django

```bash
./manage.sh create-problem \
  --code max-of-list \
  --name "Maximum of a List (R5RS)" \
  --description "Define (max-of-list lst) that returns the maximum element" \
  --time-limit 10 \
  --group Scheme \
  --types "Recursion,Lists" \
  --languages RKT
```

**Important**: Use `--time-limit 10` (or higher) — the R5RS sandbox takes ~2 seconds to start.

### tests.rkt format

```scheme
(test "test name" <expression> <expected-value>)
(test "error case" <expression> error)
```

- `<expression>` is evaluated in the R5RS sandbox where the student's code is loaded
- `<expected-value>` is compared with `equal?`
- The keyword `error` means the test expects an exception
- Number of `(test ...)` forms must match the number of entries in `init.yml`

### init.yml format

```yaml
custom_judge: grader.py
test_cases:
  - {points: 10}
  - {points: 10}
```

No `in`/`out` files needed. Points must sum to 100.

### Student feedback

| Scenario | Verdict | Feedback |
|----------|---------|----------|
| `#lang racket` in submission | WA | "Non-R5RS language detected" |
| Syntax error in student code | IR | Racket error message |
| Non-R5RS construct (e.g. `struct`) | IR | "unbound identifier: struct" |
| `#%require racket/base` | IR | Blocked by sandbox |
| Test passes | AC | Test name |
| Wrong result | WA | "expected 42 got 7" |
| Unexpected exception | WA | Exception message |
| Expected error, got error | AC | Test name |
| Wrapper TLE/MLE | TLE/MLE | Standard DMOJ message |

### Creating a new unit-test problem

1. Create `scheme-example/my-problem/`
2. Write `tests.rkt` with `(test ...)` forms
3. Create `init.yml` with `custom_judge: grader.py` and matching test case count
4. Write `solution.rkt` (pure R5RS, no `#lang`, no I/O) to verify correctness
5. Deploy: `./manage.sh deploy-scheme-problem my-problem`
6. Create in Django with `--time-limit 10`

---

## All create-problem options

| Option           | Default          | Description                    |
|------------------|------------------|--------------------------------|
| `--code`         | (required)       | Slug, must match folder in `data/problems/` |
| `--name`         | (required)       | Display name                   |
| `--description`  | `Problem: <name>`| Problem statement              |
| `--time-limit`   | `2.0`            | Seconds (use 10+ for unit-test problems) |
| `--memory-limit` | `262144`         | KB (262144 = 256 MB)           |
| `--points`       | `1.0`            | Base points                    |
| `--group`        | `Uncategorized`  | Category name (one per problem) |
| `--types`        | (none)           | Comma-separated tags (e.g. `Recursion,Lists,guia_1`) |
| `--languages`    | all              | Comma-separated keys (e.g. `RKT,PY3`) |
| `--private`      | (public)         | Do not make the problem public |
