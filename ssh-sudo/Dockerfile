FROM rust:1.90-bookworm@sha256:3914072ca0c3b8aad871db9169a651ccfce30cf58303e5d6f2db16d1d8a7e58f

RUN apt-get update && apt-get install -y --no-install-recommends libpam0g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/z4yx/pam_rssh.git /src \
    && cd /src \
    && git checkout e8dd046c423f85df266c23bcc3d7033bfee81255 \
    && git submodule update --init --recursive
WORKDIR /src
RUN cargo build --release --locked -j 2 \
    && ldd target/release/libpam_rssh.so \
    && readelf -l target/release/libpam_rssh.so
