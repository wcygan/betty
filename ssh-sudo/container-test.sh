#!/usr/bin/env bash
set -euo pipefail

useradd -m -s /bin/bash -G sudo wcygan
printf '%s\n' 'wcygan ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
printf '%s\n' 'wcygan ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/010_pi-nopasswd
cp /etc/sudoers /tmp/original-sudoers
cp /etc/pam.d/sudo /tmp/original-pam
mkdir /tmp/stage
cp /src/target/release/libpam_rssh.so /tmp/stage/
ssh-keygen -q -t ed25519 -N '' -f /home/wcygan/test-key
chown wcygan:wcygan /home/wcygan/test-key*
cp /home/wcygan/test-key.pub /tmp/stage/admin.pub
sha256sum /tmp/stage/libpam_rssh.so | cut -d ' ' -f 1 > /tmp/module-sha256

runuser -u wcygan -- ssh-agent bash -eu -c '
    ssh-add ~/test-key
    sudo python3 /test/install.py install --stage /tmp/stage \
      --sha256 "$(cat /tmp/module-sha256)" --socket "$SSH_AUTH_SOCK"
    sudo -k -n /usr/bin/id -u | grep -qx 0
    if env -u SSH_AUTH_SOCK sudo -k -n /usr/bin/id -u; then
        echo "FAIL: missing agent bypass"; exit 1
    fi
    sudo -k -n python3 /test/install.py install --stage /tmp/stage \
      --sha256 "$(cat /tmp/module-sha256)" --socket "$SSH_AUTH_SOCK"
'

backup=$(find /var/backups/ssh-sudo -mindepth 1 -maxdepth 1 -type d | sort | head -1)
python3 /test/install.py rollback --backup "$backup"
cmp /etc/sudoers /tmp/original-sudoers
cmp /etc/pam.d/sudo /tmp/original-pam
test ! -e /etc/sudoers.d/90-ssh-sudo
test ! -e /usr/lib/aarch64-linux-gnu/security/libpam_rssh.so
test ! -e /etc/security/ssh-sudo/wcygan.keys

if python3 /test/install.py install --stage /tmp/stage --sha256 invalid --socket /not-an-agent; then
    echo 'FAIL: accepted tampered module'; exit 1
fi
cmp /etc/sudoers /tmp/original-sudoers

if python3 /test/install.py install --stage /tmp/stage \
    --sha256 "$(cat /tmp/module-sha256)" --socket /not-an-agent; then
    echo 'FAIL: accepted missing agent'; exit 1
fi
cmp /etc/sudoers /tmp/original-sudoers
cmp /etc/pam.d/sudo /tmp/original-pam
test ! -e /etc/sudoers.d/90-ssh-sudo
echo 'PASS: real PAM signing, sudo, denial, idempotency, rollback, digest rejection, failed-install recovery'
