FROM python:3.11-slim

# System deps for building dmoj judge + sandbox + networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libseccomp-dev \
    netcat-openbsd \
    # Language runtimes (Python 3 comes from base image)
    racket \
    swi-prolog \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m judge

# Install DMOJ judge in a venv
RUN python3 -m venv /env && \
    /env/bin/pip3 install cython setuptools && \
    /env/bin/pip3 install dmoj

# Patch isolate.py to fix Racket sandbox bug (remove once dmoj > 4.1.0)
COPY patch_isolate.py /tmp/patch_isolate.py
RUN python3 /tmp/patch_isolate.py && rm /tmp/patch_isolate.py

RUN mkdir -p /judge /problems /tmp/judge_cache && \
    chown -R judge:judge /judge /problems /tmp/judge_cache

COPY start-judge.sh /judge/start-judge.sh
COPY scheme_grader.py /judge/scheme_grader.py
RUN sed -i 's/\r//' /judge/start-judge.sh && \
    chmod +x /judge/start-judge.sh && \
    chown judge:judge /judge/start-judge.sh /judge/scheme_grader.py

WORKDIR /judge

CMD ["/judge/start-judge.sh"]
