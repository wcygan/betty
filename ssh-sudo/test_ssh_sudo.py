import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[1]
harness = load("ssh_sudo", ROOT / "scripts/ssh_sudo.py")
installer = load("ssh_sudo_install", ROOT / "ssh-sudo/install.py")


def result(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class IntegrationHarnessTests(unittest.TestCase):
    def test_accepts_root_execution_and_two_denials(self):
        replies = [result(stdout="256 SHA256:example admin (ED25519)"),
                   result(stdout="0\n"), result(1, stderr="sudo: a password is required"),
                   result(1, stderr="sudo: a password is required")]
        with patch.object(harness, "remote", side_effect=replies):
            self.assertEqual(harness.test_host(["ssh", "-A", "betty"]),
                             "agent-only SSH, forwarding, sudo uid=0; missing-agent and no-forwarding sudo denied")

    def test_detects_passwordless_bypass(self):
        with patch.object(harness, "remote", side_effect=[result(), result(stdout="0"), result(stdout="0")]):
            with self.assertRaisesRegex(RuntimeError, "NOPASSWD"):
                harness.test_host(["ssh", "-A", "gertrude"])

    def test_does_not_mistake_ssh_failure_for_denial(self):
        replies = [result(), result(stdout="0"), result(1, stderr="sudo: a password is required"),
                   result(255, stderr="ssh: authentication failed")]
        with patch.object(harness, "remote", side_effect=replies):
            with self.assertRaisesRegex(RuntimeError, "inconclusive"):
                harness.test_host(["ssh", "-A", "gertrude"])

    def test_rejects_non_root_result(self):
        with patch.object(harness, "remote", side_effect=[result(), result(stdout="1000")]):
            with self.assertRaisesRegex(RuntimeError, "did not run as root"):
                harness.test_host(["ssh", "-A", "betty"])


class PolicyTests(unittest.TestCase):
    def test_migrates_only_observed_user_bypass(self):
        original = "root ALL=(ALL) ALL\nwcygan ALL=(ALL) NOPASSWD: ALL\nbackup ALL=(root) NOPASSWD: /usr/bin/rsync\n"
        self.assertEqual(installer.remove_known_bypass(original),
                         "root ALL=(ALL) ALL\nbackup ALL=(root) NOPASSWD: /usr/bin/rsync\n")

    def test_retains_existing_password_authentication(self):
        original = "#%PAM-1.0\nauth include system-auth\naccount include system-auth\n"
        expected = ("# Managed by betty/ssh-sudo/install.py\n"
                    "auth sufficient /lib/security/libpam_rssh.so auth_key_file=/etc/security/ssh-sudo/${user}.keys\n"
                    "#%PAM-1.0\nauth include system-auth\naccount include system-auth\n")
        first = installer.pam_content(original, "/lib/security/libpam_rssh.so")
        self.assertEqual(first, expected)
        self.assertEqual(installer.pam_content(first, "/lib/security/libpam_rssh.so"), expected)

    def test_rejects_unmanaged_pam_integration(self):
        with self.assertRaisesRegex(ValueError, "Unmanaged"):
            installer.pam_content("auth sufficient pam_ssh_agent_auth.so\n", "/lib/module.so")


class MacConfigurationTests(unittest.TestCase):
    def test_migration_preserves_other_hosts_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            directory = home / ".ssh"
            directory.mkdir()
            path = directory / "config"
            prefix = 'Include ~/.orbstack/ssh/config\nHost *\n\tIdentityAgent "1password.sock"\n\n'
            original = (prefix + 'Host betty\n\tForwardAgent yes\n\nHost betty gertrude\n'
                        '\tUser wcygan\n\tIdentityFile ~/.ssh/id_ed25519\n')
            path.write_text(original)
            with patch.object(harness.Path, "home", return_value=home):
                harness.configure_mac("ssh-ed25519 PUBLIC admin\n")
                expected = (prefix + 'Host betty gertrude\n\tUser wcygan\n'
                            '\tIdentityFile ~/.ssh/1password-admin.pub\n'
                            '\tIdentitiesOnly yes\n\tForwardAgent yes\n')
                self.assertEqual(path.read_text(), expected)
                harness.configure_mac("ssh-ed25519 PUBLIC admin\n")
                self.assertEqual(path.read_text(), expected)
            self.assertEqual(next(directory.glob("config.before-ssh-sudo-*")).read_text(), original)
            self.assertEqual((directory / "1password-admin.pub").read_text(), "ssh-ed25519 PUBLIC admin\n")

    def test_unknown_config_is_left_intact(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            directory = home / ".ssh"
            directory.mkdir()
            path = directory / "config"
            path.write_text("Host special\n    ProxyJump jump.example\n")
            with patch.object(harness.Path, "home", return_value=home):
                with self.assertRaisesRegex(RuntimeError, "differs from the inspected baseline"):
                    harness.configure_mac("ssh-ed25519 PUBLIC admin\n")
            self.assertEqual(path.read_text(), "Host special\n    ProxyJump jump.example\n")


if __name__ == "__main__":
    unittest.main()
