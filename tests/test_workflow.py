"""ShanShell AI 工作流预测引擎测试。"""

import unittest

from shansh.workflow_engine import WorkflowEngine


class TestWorkflowEngine(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()

    def test_git_add_predicts_git_commit(self):
        result = self.engine.predict(["ls", "git add ."])
        self.assertTrue(len(result) > 0)
        self.assertIn("git commit -m", result[0].cmd)

    def test_git_commit_predicts_git_push(self):
        result = self.engine.predict(["git add .", "git commit -m \"fix\""])
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "git push")

    def test_venv_predicts_source_activate(self):
        result = self.engine.predict(["python -m venv .venv"])
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "source .venv/bin/activate")

    def test_source_activate_with_requirements_txt(self):
        context = {"files": ["requirements.txt", "main.py"]}
        result = self.engine.predict(["source .venv/bin/activate"], context)
        self.assertTrue(len(result) > 0)
        self.assertIn("pip install -r requirements.txt", result[0].cmd)

    def test_source_activate_without_requirements_txt(self):
        context = {"files": ["main.py"]}
        result = self.engine.predict(["source .venv/bin/activate"], context)
        self.assertTrue(len(result) == 0)

    def test_dnf_install_predicts_systemctl_enable(self):
        result = self.engine.predict(["sudo dnf install nginx"])
        self.assertTrue(len(result) > 0)
        self.assertIn("systemctl enable --now nginx", result[0].cmd)

    def test_systemctl_enable_predicts_status(self):
        result = self.engine.predict(["systemctl enable --now nginx"])
        self.assertTrue(len(result) > 0)
        self.assertIn("systemctl status nginx", result[0].cmd)

    def test_docker_build_predicts_docker_run(self):
        result = self.engine.predict(["docker build -t myapp ."])
        self.assertTrue(len(result) > 0)
        self.assertIn("docker run --rm myapp", result[0].cmd)

    def test_git_clone_predicts_cd(self):
        result = self.engine.predict(["git clone https://github.com/user/repo.git"])
        self.assertTrue(len(result) > 0)
        self.assertIn("cd repo", result[0].cmd)

    def test_git_clone_without_git_suffix(self):
        result = self.engine.predict(["git clone https://github.com/user/repo"])
        self.assertTrue(len(result) > 0)
        self.assertIn("cd repo", result[0].cmd)

    def test_tar_predicts_ls(self):
        result = self.engine.predict(["tar -czvf backup.tar.gz /data"])
        self.assertTrue(len(result) > 0)
        self.assertIn("ls -lh backup.tar.gz", result[0].cmd)

    def test_empty_last_commands(self):
        result = self.engine.predict([])
        self.assertEqual(len(result), 0)

    def test_no_prediction_for_unknown(self):
        result = self.engine.predict(["some random command"])
        self.assertEqual(len(result), 0)

    def test_candidate_has_explanation(self):
        result = self.engine.predict(["git add ."])
        self.assertTrue(len(result) > 0)
        self.assertTrue(len(result[0].explanation) > 0)

    def test_candidate_has_to_dict(self):
        result = self.engine.predict(["git add ."])
        d = result[0].to_dict()
        self.assertIn("cmd", d)
        self.assertIn("explanation", d)


class TestWorkflowWithHistory(unittest.TestCase):
    def test_empty_buffer_with_history_predicts_next(self):
        from shansh.stats import record_command
        record_command("git add .", exit_code=0, cwd=".")

        from shansh.context import collect_context
        ctx = collect_context("", ".")

        engine = WorkflowEngine()
        result = engine.predict(ctx.get("last_commands", []), ctx)
        self.assertTrue(len(result) > 0)
        self.assertIn("git commit -m", result[0].cmd)

    def test_venv_history_predicts_activate(self):
        from shansh.stats import record_command
        record_command("python -m venv .venv", exit_code=0, cwd=".")

        from shansh.context import collect_context
        ctx = collect_context("", ".")

        engine = WorkflowEngine()
        result = engine.predict(ctx.get("last_commands", []), ctx)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0].cmd, "source .venv/bin/activate")


if __name__ == "__main__":
    unittest.main()
