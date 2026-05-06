"""ShanShell AI 命令补全引擎测试。"""

import unittest

from shansh.completion_engine import CompletionEngine


class TestCompletionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CompletionEngine()

    def test_git_st_completes_to_git_status(self):
        result = self.engine.complete("git st")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "git status")
        self.assertEqual(result[0].ghost_text, "atus")

    def test_git_sta_completes_to_git_status(self):
        result = self.engine.complete("git sta")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "git status")

    def test_git_co_returns_three_candidates(self):
        result = self.engine.complete("git co")
        self.assertEqual(len(result), 3)
        cmds = [c.cmd for c in result]
        self.assertIn("git commit", cmds)
        self.assertIn("git checkout", cmds)
        self.assertIn("git clone", cmds)

    def test_git_p_returns_push_and_pull(self):
        result = self.engine.complete("git p")
        self.assertEqual(len(result), 2)
        cmds = [c.cmd for c in result]
        self.assertIn("git push", cmds)
        self.assertIn("git pull", cmds)

    def test_dnf_ins_completes_to_sudo_dnf_install(self):
        result = self.engine.complete("dnf ins")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "sudo dnf install")

    def test_dnf_se_completes_to_dnf_search(self):
        result = self.engine.complete("dnf se")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "dnf search")

    def test_dnf_up_completes_to_sudo_dnf_upgrade(self):
        result = self.engine.complete("dnf up")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "sudo dnf upgrade")

    def test_systemctl_sta_completes_to_status(self):
        result = self.engine.complete("systemctl sta")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "systemctl status")

    def test_systemctl_en_completes_to_enable_now(self):
        result = self.engine.complete("systemctl en")
        self.assertTrue(len(result) > 0)
        self.assertIn("sudo systemctl enable --now", result[0].cmd)

    def test_systemctl_re_completes_to_restart(self):
        result = self.engine.complete("systemctl re")
        self.assertTrue(len(result) > 0)
        self.assertIn("restart", result[0].cmd)

    def test_docker_ps_dash_completes_to_ps_a(self):
        result = self.engine.complete("docker ps -")
        self.assertTrue(len(result) > 0)
        self.assertIn("docker ps -a", result[0].cmd)

    def test_docker_ru_completes_to_run_rm(self):
        result = self.engine.complete("docker ru")
        self.assertTrue(len(result) > 0)
        self.assertIn("docker run --rm", result[0].cmd)

    def test_docker_im_completes_to_images(self):
        result = self.engine.complete("docker im")
        self.assertTrue(len(result) > 0)
        self.assertIn("docker images", result[0].cmd)

    def test_pytest_completes_to_q(self):
        result = self.engine.complete("pytest")
        self.assertTrue(len(result) > 0)
        self.assertIn("pytest -q", result[0].cmd)

    def test_python_m_with_main_py(self):
        context = {"files": ["main.py", "README.md"]}
        result = self.engine.complete("python m", context)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "python main.py")

    def test_python_m_without_main_py(self):
        context = {"files": ["README.md"]}
        result = self.engine.complete("python m", context)
        self.assertEqual(len(result), 0)

    def test_pip_install_r_with_requirements_txt(self):
        context = {"files": ["requirements.txt"]}
        result = self.engine.complete("pip install -r", context)
        self.assertTrue(len(result) > 0)
        self.assertIn("requirements.txt", result[0].cmd)

    def test_npm_r_with_package_json(self):
        context = {"files": ["package.json"]}
        result = self.engine.complete("npm r", context)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "npm run dev")

    def test_npm_i_completes_to_install(self):
        result = self.engine.complete("npm i")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "npm install")

    def test_make_with_makefile(self):
        context = {"files": ["Makefile"]}
        result = self.engine.complete("make", context)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "make all")

    def test_docker_bu_with_dockerfile(self):
        context = {"files": ["Dockerfile"], "cwd": "/root/myapp"}
        result = self.engine.complete("docker bu", context)
        self.assertTrue(len(result) > 0)
        self.assertIn("myapp", result[0].cmd)
        self.assertIn("docker build -t", result[0].cmd)

    def test_docker_bu_without_dockerfile(self):
        context = {"files": ["README.md"], "cwd": "/root/myapp"}
        result = self.engine.complete("docker bu", context)
        self.assertEqual(len(result), 0)

    def test_cd_subdirs(self):
        import os, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "src"), exist_ok=True)
            os.makedirs(os.path.join(tmp, "tests"), exist_ok=True)
            os.makedirs(os.path.join(tmp, "docs"), exist_ok=True)
            open(os.path.join(tmp, "file.txt"), "w").close()
            context = {"cwd": tmp, "files": os.listdir(tmp)}
            result = self.engine.complete("cd", context)
            self.assertTrue(len(result) > 0)
            names = [c.cmd for c in result]
            self.assertIn("cd docs", names)

    def test_python_dash_m_with_python_project(self):
        context = {"files": ["main.py", "requirements.txt"], "project_types": ["python"]}
        result = self.engine.complete("python -m", context)
        self.assertTrue(len(result) > 0)
        self.assertIn("pytest", result[0].cmd)

    def test_git_br_completes_to_branch(self):
        result = self.engine.complete("git br")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "git branch")

    def test_git_ch_completes_to_checkout(self):
        result = self.engine.complete("git ch")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "git checkout")

    def test_git_sw_completes_to_switch(self):
        result = self.engine.complete("git sw")
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "git switch")

    def test_empty_buffer_returns_empty(self):
        result = self.engine.complete("")
        self.assertEqual(len(result), 0)

    def test_unknown_command_returns_empty(self):
        result = self.engine.complete("xyzabc 123")
        self.assertEqual(len(result), 0)

    def test_candidate_has_to_dict(self):
        result = self.engine.complete("git st")
        d = result[0].to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("cmd", d)
        self.assertIn("confidence", d)


if __name__ == "__main__":
    unittest.main()
