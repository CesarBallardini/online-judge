"""
Patch dmoj isolate.py to fix Racket executor sandbox bug.

The Racket executor's self-test fails with:
  AssertionError: Must pass a normalized, absolute path to check
  Protection fault on: 89 (sys_readlink)

Root cause: os.path.realpath() returns paths that aren't normalized the way
fs_jail.check() requires. Racket heavily uses symlinks under
/usr/share/racket/collects/.

Remove this patch once dmoj > 4.1.0 is released with upstream fixes.
"""

import glob
import sys

# Find the installed isolate.py
candidates = glob.glob("/env/lib/python*/site-packages/dmoj/cptbox/isolate.py")
if not candidates:
    print("ERROR: Could not find isolate.py", file=sys.stderr)
    sys.exit(1)

path = candidates[0]
print(f"Patching {path}")

with open(path, "r") as f:
    src = f.read()

# --- Patch A: Add /memfd: guard to samefile comparison ---
old_a = "same = normalized == real or os.path.samefile(projected, real)"
new_a = "same = normalized == real or real.startswith('/memfd:') or os.path.samefile(projected, real)"
assert old_a in src, f"Patch A target not found in {path}"
src = src.replace(old_a, new_a, 1)

# --- Patch B: Fix /proc/self/. normalization + normalize real + /memfd: guard ---
old_b = """\
            if real.startswith(proc_dir):
                real = os.path.join('/proc/self', os.path.relpath(real, proc_dir))

            if not fs_jail.check(real):
                raise DeniedSyscall(ACCESS_EACCES, f'Denying {file}, real path {real}')"""

new_b = """\
            if real.startswith(proc_dir):
                relpath = os.path.relpath(real, proc_dir)
                if relpath == '.':
                    real = '/proc/self'
                else:
                    real = os.path.join('/proc/self', relpath)

            real = '/' + os.path.normpath(real).lstrip('/')
            if not real.startswith('/memfd:') and not fs_jail.check(real):
                raise DeniedSyscall(ACCESS_EACCES, f'Denying {file}, real path {real}')"""

assert old_b in src, f"Patch B target not found in {path}"
src = src.replace(old_b, new_b, 1)

with open(path, "w") as f:
    f.write(src)

print("Patches applied successfully.")
