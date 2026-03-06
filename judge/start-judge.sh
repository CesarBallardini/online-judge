#!/bin/bash
set -e

# Wait for bridged service to be available
echo "Waiting for DMOJ bridged service..."
while ! nc -z bridged 9999 2>/dev/null; do
  echo "Bridged service not ready, waiting..."
  sleep 5
done
echo "Bridged service is up!"

# Auto-detect available language runtimes
echo "Auto-detecting language runtimes..."
dmoj-autoconf > /judge/runtime.yml 2>/dev/null || true

echo "--- Detected runtimes ---"
cat /judge/runtime.yml
echo "-------------------------"

# Create judge configuration from environment variables + detected runtimes
cat > /judge/judge.yml << EOF
id: ${JUDGE_NAME}
key: ${JUDGE_KEY}
problem_storage_root: /problems
EOF

# Append runtime config if any runtimes were detected
if [ -s /judge/runtime.yml ]; then
    echo "" >> /judge/judge.yml
    cat /judge/runtime.yml >> /judge/judge.yml
fi

echo "--- Final judge.yml ---"
cat /judge/judge.yml
echo "-----------------------"

# Start the judge
echo "Starting judge: ${JUDGE_NAME}"
exec dmoj -c /judge/judge.yml -p 9999 bridged
