FROM betty-pam-rssh:1.2.1
RUN apt-get update && apt-get install -y --no-install-recommends sudo openssh-client python3 \
    && rm -rf /var/lib/apt/lists/*
