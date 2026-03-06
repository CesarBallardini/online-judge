FROM python:3.11-slim

USER root

# Install system dependencies and language runtimes
RUN apt-get update && apt-get install -y \
    # Build tools
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libseccomp-dev \
    git \
    curl \
    netcat-openbsd \
    # Language runtimes
    default-jdk-headless \
    ruby \
    php-cli \
    perl \
    rustc \
    ghc \
    golang-go \
    mono-mcs \
    fp-compiler \
    nasm \
    lua5.4 \
    swi-prolog \
    gawk \
    sed \
    bc \
    && rm -rf /var/lib/apt/lists/*

# Update pip and install DMOJ judge + Python support
RUN pip install --upgrade pip && pip install dmoj

# Create judge user
RUN useradd -m -U judge

# Create necessary directories and set permissions
RUN mkdir -p /judge /problems /tmp/judge_cache && \
    chown -R judge:judge /judge /problems /tmp/judge_cache

# Copy startup script
COPY start-judge.sh /judge/start-judge.sh
RUN sed -i 's/\r//' /judge/start-judge.sh && \
    chmod +x /judge/start-judge.sh && \
    chown judge:judge /judge/start-judge.sh

WORKDIR /judge
USER judge

EXPOSE 9999

CMD ["/judge/start-judge.sh"]
