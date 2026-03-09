# Scheme Problems

This folder contains problems designed for Racket (Scheme). Each subfolder is a self-contained problem with test cases ready to deploy to the DMOJ judge.

## Folder Structure

```
scheme-example/
├── README.md
└── max-of-numbers/
    ├── init.yml          # DMOJ test case config
    ├── solution.rkt      # Reference solution
    ├── 1.in / 1.out      # Test case 1 (empty list)
    ├── 2.in / 2.out      # Test case 2 (one number)
    └── ...
```

## How to Deploy a Problem

### 1. Copy test data to the problems volume

```bash
cp -r scheme-example/max-of-numbers/ data/problems/max-of-numbers/
```

This makes `init.yml` and the `.in/.out` files visible to the judge at `/problems/max-of-numbers/`.

### 2. Create the problem record in Django

```bash
./manage.sh create-problem \
  --code max-of-numbers \
  --name "Maximum of a List" \
  --description "Given a list of integers find the maximum" \
  --group Scheme \
  --types "Recursion,Lists,guia_1" \
  --languages RKT
```

This creates the problem, tags it with types, and restricts submissions to Racket only. To allow all languages, omit `--languages`. To keep the problem hidden, add `--private`.

All options:

| Option           | Default          | Description                    |
|------------------|------------------|--------------------------------|
| `--code`         | (required)       | Slug, must match folder in `data/problems/` |
| `--name`         | (required)       | Display name                   |
| `--description`  | `Problem: <name>`| Problem statement              |
| `--time-limit`   | `2.0`            | Seconds                        |
| `--memory-limit` | `262144`         | KB (262144 = 256 MB)           |
| `--points`       | `1.0`            | Base points                    |
| `--group`        | `Uncategorized`  | Category name (one per problem) |
| `--types`        | (none)           | Comma-separated tags (e.g. `Recursion,Lists,guia_1`) |
| `--languages`    | all              | Comma-separated keys (e.g. `RKT,PY3`) |
| `--private`      | (public)         | Do not make the problem public |

### 3. Verify

The problem should now appear at `http://localhost/problems/` and accept submissions.

## Test Case Format (init.yml)

```yaml
test_cases:
  - {in: 1.in, out: 1.out, points: 10}
  - {in: 2.in, out: 2.out, points: 10}
```

Input/output files can be named anything as long as `init.yml` references them correctly. Points must sum to 100.

## Creating a New Problem

1. Create a folder: `scheme-example/my-problem/`
2. Write test cases as `.in` / `.out` pairs
3. Create `init.yml` listing the test cases and points
4. Write a `solution.rkt` to verify correctness
5. Test locally: `for i in 1 2 3; do racket solution.rkt < $i.in | diff - $i.out; done`
6. Deploy using steps 1-3 above
