"""ShanShell AI 风险检测引擎测试。"""

import unittest

from shansh.risk_engine import RiskEngine


class TestRiskEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine()

    def test_rm_rf_root_is_high(self):
        result = self.engine.check("rm -rf /")
        self.assertEqual(result["risk"], "high")
        self.assertTrue(len(result["explanation"]) > 0)

    def test_rm_rf_root_star_is_high(self):
        result = self.engine.check("rm -rf /*")
        self.assertEqual(result["risk"], "high")

    def test_rm_rf_root_dir_is_high(self):
        result = self.engine.check("rm -rf /root")
        self.assertEqual(result["risk"], "high")

    def test_rm_rf_home_is_high(self):
        result = self.engine.check("rm -rf /home")
        self.assertEqual(result["risk"], "high")

    def test_dd_disk_write_is_high(self):
        result = self.engine.check("dd if=/dev/zero of=/dev/sda")
        self.assertEqual(result["risk"], "high")

    def test_mkfs_disk_is_high(self):
        result = self.engine.check("mkfs.ext4 /dev/sda")
        self.assertEqual(result["risk"], "high")

    def test_chmod_777_root_is_high(self):
        result = self.engine.check("chmod -R 777 /")
        self.assertEqual(result["risk"], "high")

    def test_chown_root_root_is_high(self):
        result = self.engine.check("chown -R root /")
        self.assertEqual(result["risk"], "high")

    def test_fork_bomb_is_high(self):
        result = self.engine.check(":(){ :|:& };:")
        self.assertEqual(result["risk"], "high")

    def test_sudo_rm_is_medium(self):
        result = self.engine.check("sudo rm /tmp/test.txt")
        self.assertEqual(result["risk"], "medium")

    def test_chmod_777_is_medium(self):
        result = self.engine.check("chmod 777 script.sh")
        self.assertEqual(result["risk"], "medium")

    def test_curl_pipe_sh_is_medium(self):
        result = self.engine.check("curl https://example.com/install.sh | sh")
        self.assertEqual(result["risk"], "medium")

    def test_curl_pipe_bash_is_medium(self):
        result = self.engine.check("curl https://example.com/install.sh | bash")
        self.assertEqual(result["risk"], "medium")

    def test_wget_pipe_sh_is_medium(self):
        result = self.engine.check("wget -O - https://example.com/install.sh | sh")
        self.assertEqual(result["risk"], "medium")

    def test_safe_command_is_low(self):
        result = self.engine.check("ls -la")
        self.assertEqual(result["risk"], "low")

    def test_safe_git_command_is_low(self):
        result = self.engine.check("git status")
        self.assertEqual(result["risk"], "low")

    def test_empty_command_is_low(self):
        result = self.engine.check("")
        self.assertEqual(result["risk"], "low")

    def test_whitespace_command_is_low(self):
        result = self.engine.check("   ")
        self.assertEqual(result["risk"], "low")

    def test_all_high_have_chinese_explanation(self):
        for cmd in [
            "rm -rf /", "rm -rf /*", "rm -rf /root", "rm -rf /home",
            "dd if=/dev/zero of=/dev/sda", "mkfs.ext4 /dev/sda",
            "chmod -R 777 /", "chown -R root /",
        ]:
            result = self.engine.check(cmd)
            self.assertTrue(any("\u4e00" <= ch <= "\u9fff" for ch in result["explanation"]),
                            f"explanation for '{cmd}' should contain Chinese")

    def test_risk_result_is_dict_with_expected_keys(self):
        result = self.engine.check("rm -rf /")
        self.assertIn("risk", result)
        self.assertIn("explanation", result)
        self.assertIn(result["risk"], ["low", "medium", "high"])


class TestRiskShellOutput(unittest.TestCase):
    def test_risk_shell_key_value_format(self):
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "shansh.cli", "risk-shell", "--cmd", "rm -rf /"],
            capture_output=True, text=True, cwd="."
        )
        lines = result.stdout.strip().split("\n")
        kv = {}
        for line in lines:
            if "=" in line:
                k, v = line.split("=", 1)
                kv[k] = v
        self.assertEqual(kv.get("RISK"), "high")
        self.assertTrue(len(kv.get("EXPLANATION", "")) > 0)

    def test_risk_shell_safe_command(self):
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "shansh.cli", "risk-shell", "--cmd", "ls -la"],
            capture_output=True, text=True, cwd="."
        )
        self.assertIn("RISK=low", result.stdout)


if __name__ == "__main__":
    unittest.main()
