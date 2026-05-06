"""ShanShell AI 命令纠错引擎测试。"""

import unittest

from shansh.correction_engine import CorrectionEngine


class TestCorrectionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CorrectionEngine()

    def test_gti_corrects_to_git(self):
        result = self.engine.correct("gti statsu")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertEqual(result["candidates"][0].cmd, "git status")
        self.assertTrue(len(result["diagnostics"]) > 0)

    def test_statsu_corrects_to_status(self):
        result = self.engine.correct("git statsu")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("status", result["candidates"][0].cmd)

    def test_mkidr_corrects_to_mkdir(self):
        result = self.engine.correct("mkidr test")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("mkdir", result["candidates"][0].cmd)

    def test_apt_install_nginx_to_sudo_dnf_install_nginx(self):
        result = self.engine.correct("apt install nginx")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("sudo dnf install nginx", result["candidates"][0].cmd)

    def test_apt_install_ng_to_sudo_dnf_install_nginx(self):
        result = self.engine.correct("apt install ng")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("sudo dnf install nginx", result["candidates"][0].cmd)

    def test_ls_z_home_corrects_flag(self):
        result = self.engine.correct("ls -z /home")
        self.assertTrue(len(result["diagnostics"]) > 0)
        self.assertEqual(result["diagnostics"][0].severity, "warning")
        self.assertIn("-l", result["replacement"])

    def test_nl_disk_space_to_df(self):
        result = self.engine.correct("查看磁盘空间")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("df -h", result["candidates"][0].cmd)

    def test_nl_memory_to_free(self):
        result = self.engine.correct("查看内存")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("free -h", result["candidates"][0].cmd)

    def test_tar_extract(self):
        result = self.engine.correct("解压 test.tar.gz")
        self.assertTrue(len(result["candidates"]) > 0)
        self.assertIn("tar -zxvf test.tar.gz", result["candidates"][0].cmd)

    def test_diagnostic_has_correct_fields(self):
        result = self.engine.correct("gti statsu")
        self.assertTrue(len(result["diagnostics"]) > 0)
        d = result["diagnostics"][0]
        self.assertIsInstance(d.start, int)
        self.assertIsInstance(d.end, int)
        self.assertIsInstance(d.severity, str)
        self.assertIsInstance(d.message, str)

    def test_empty_buffer(self):
        result = self.engine.correct("")
        self.assertEqual(len(result["candidates"]), 0)
        self.assertEqual(len(result["diagnostics"]), 0)

    def test_no_correction_needed(self):
        result = self.engine.correct("git status")
        self.assertEqual(len(result["candidates"]), 0)

    def test_diagnostic_to_dict(self):
        result = self.engine.correct("gti statsu")
        d = result["diagnostics"][0].to_dict()
        self.assertIn("start", d)
        self.assertIn("end", d)
        self.assertIn("severity", d)
        self.assertIn("message", d)


if __name__ == "__main__":
    unittest.main()
