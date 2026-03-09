#!/bin/bash
set -e

echo "Waiting for DMOJ bridged service..."
while ! nc -z bridged 9999 2>/dev/null; do
  echo "Bridged service not ready, waiting..."
  sleep 5
done
echo "Bridged service is up!"

# Detect runtimes at startup (needs privileged mode for sandbox self-tests)
echo "Detecting language runtimes..."
/env/bin/dmoj-autoconf -V > /judge/runtime.yml 2>/dev/null || true

# Create judge config
cat > /judge/judge.yml << EOF
id: ${JUDGE_NAME}
key: ${JUDGE_KEY}
problem_storage_root: /problems
EOF

if [ -s /judge/runtime.yml ]; then
    echo "" >> /judge/judge.yml
    cat /judge/runtime.yml >> /judge/judge.yml
fi

echo "--- Final judge.yml ---"
cat /judge/judge.yml
echo "-----------------------"

echo "Starting judge: ${JUDGE_NAME}"
cd /judge
exec runuser -u judge -w PATH -- /env/bin/dmoj -c /judge/judge.yml -p 9999 bridged
