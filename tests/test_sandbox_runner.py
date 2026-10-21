"""Lifecycle safety regressions; execution follows the workspace test gate."""
from argparse import Namespace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sandbox_runner as runner


class SandboxOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.editor = base / "Engine/Binaries/Win64/UnrealEditor.exe"
        self.editor.parent.mkdir(parents=True)
        self.editor.touch()
        self.project = base / "Project/Example.uproject"
        self.project.parent.mkdir()
        self.project.write_text("{}", encoding="utf-8")
        self.state = {
            "pid": 1234,
            "created": "2026-01-01T00:00:00Z",
            "editor": str(self.editor),
            "project": str(self.project),
            "results": str(self.project.parent / "Saved/Validation"),
            "port": 58241,
            "command_line": f'"{self.editor}" "{self.project}"',
        }
        self.current = {
            "pid": self.state["pid"],
            "created": self.state["created"],
            "executable": self.state["editor"],
            "command_line": self.state["command_line"],
        }

    def test_reused_pid_cannot_be_stopped(self):
        changed = {**self.current, "created": "2026-01-02T00:00:00Z"}
        with patch.object(runner, "process_info", return_value=changed), patch.object(runner, "powershell_json") as control:
            with self.assertRaises(runner.RunnerError):
                runner.stop_owned(self.state, force=True)
            control.assert_not_called()

    def test_altered_executable_or_command_is_not_owned(self):
        for field, value in (("executable", str(self.editor.parent / "Other.exe")), ("command_line", "another project")):
            with self.subTest(field=field), self.assertRaises(runner.RunnerError):
                runner.require_owned(self.state, {**self.current, field: value})

    def test_same_identity_still_requires_the_project(self):
        state = {**self.state, "command_line": f'"{self.editor}"'}
        current = {**self.current, "command_line": state["command_line"]}
        with self.assertRaises(runner.RunnerError):
            runner.require_owned(state, current)

    def test_graceful_exit_waits_through_empty_cim_fields(self):
        terminating = {**self.current, "executable": None, "command_line": ""}
        with patch.object(runner, "process_info", side_effect=[self.current, terminating, None, None]), \
                patch.object(runner, "powershell_json") as control, \
                patch.object(runner, "port_owners", return_value=[]), \
                patch.object(runner.time, "sleep"), patch.object(runner, "write_json"):
            result = runner.stop_owned(self.state)
        self.assertEqual(result["status"], "stopped")
        self.assertIn("stopped_at", result)
        self.assertEqual(control.call_count, 1)
        self.assertIn("CloseMainWindow", control.call_args.args[0])

    def test_incomplete_identity_cannot_authorize_force(self):
        terminating = {**self.current, "executable": None, "command_line": None}
        with patch.object(runner, "process_info", side_effect=[self.current, terminating]), \
                patch.object(runner, "powershell_json") as control:
            with self.assertRaises(runner.RunnerError):
                runner.stop_owned(self.state, force=True, grace=0)
        self.assertEqual(control.call_count, 1)
        self.assertNotIn("Stop-Process", control.call_args.args[0])

    def test_changed_creation_time_is_rejected_during_exit_wait(self):
        changed = {**self.current, "created": "2026-01-02T00:00:00Z", "executable": None, "command_line": None}
        with patch.object(runner, "process_info", side_effect=[self.current, changed]), \
                patch.object(runner, "powershell_json") as control:
            with self.assertRaises(runner.RunnerError):
                runner.stop_owned(self.state)
        self.assertEqual(control.call_count, 1)

    def test_partial_identity_cannot_hide_a_known_mismatch(self):
        changed = {**self.current, "executable": None, "command_line": "different command"}
        with self.assertRaises(runner.RunnerError):
            runner.require_owned(self.state, changed, allow_terminating=True)

    def test_failed_start_uses_owned_handle_when_identity_cleanup_fails(self):
        process = Mock()
        process.poll.side_effect = [None, 1]
        original = runner.RunnerError("startup listener timeout")
        with patch.object(runner, "stop_owned", side_effect=runner.RunnerError("CIM unavailable")), \
                patch.object(runner, "port_owners", return_value=[]), patch.object(runner, "write_json"):
            result = runner.cleanup_failed_start(process, self.state, self.project.parent, self.project.parent, original, self.state["port"])
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=15)
        self.assertEqual(result["status"], "startup_failed_cleaned_up")
        self.assertIn("startup listener timeout", result["startup_error"])
        self.assertIn("CIM unavailable", result["ownership_cleanup_error"])

    def test_failed_start_preserves_unrelated_listener(self):
        process = Mock()
        process.poll.return_value = 1
        with patch.object(runner, "stop_owned", side_effect=runner.RunnerError("identity changed")), \
                patch.object(runner, "port_owners", return_value=[9999]), \
                patch.object(runner, "powershell_json") as control, patch.object(runner, "write_json"):
            result = runner.cleanup_failed_start(process, self.state, self.project.parent, self.project.parent,
                                                 runner.RunnerError("startup failed"), self.state["port"])
        process.terminate.assert_not_called()
        control.assert_not_called()
        self.assertEqual(result["status"], "startup_failed_cleanup_incomplete")
        self.assertEqual(result["port_owners_after_cleanup"], [9999])

    def test_failed_start_reports_handle_and_record_errors_separately(self):
        process = Mock()
        process.poll.return_value = None
        process.terminate.side_effect = OSError("handle terminate failed")
        with patch.object(runner, "stop_owned", side_effect=runner.RunnerError("inspection failed")), \
                patch.object(runner, "port_owners", side_effect=runner.RunnerError("port inspection failed")), \
                patch.object(runner, "write_json", side_effect=OSError("disk unavailable")):
            result = runner.cleanup_failed_start(process, self.state, self.project.parent, self.project.parent,
                                                 runner.RunnerError("original start failure"), self.state["port"])
        self.assertIn("original start failure", result["startup_error"])
        self.assertIn("handle terminate failed", result["handle_cleanup_error"])
        self.assertIn("port inspection failed", result["port_inspection_error"])
        self.assertEqual(len(result["record_errors"]), 2)
        self.assertEqual(result["status"], "startup_failed_cleanup_incomplete")
        self.assertNotIn("stopped_at", self.state)

    def test_results_cannot_escape_project_saved(self):
        args = Namespace(project=str(self.project), engine=str(self.editor.parents[2]),
                         results=str(self.project.parent / "Content/Results"), port=58241, codex_executable=None)
        with self.assertRaises(runner.RunnerError):
            runner.resolve_inputs(args)

    def test_concurrent_lifecycle_is_rejected_and_outer_lock_survives(self):
        results = self.project.parent / "Saved/Validation"
        with runner.lifecycle_lock(results):
            with self.assertRaises(runner.RunnerError):
                with runner.lifecycle_lock(results):
                    self.fail("A concurrent lifecycle operation was admitted")
            self.assertTrue((results / "lifecycle.lock").is_file())
        self.assertFalse((results / "lifecycle.lock").exists())


if __name__ == "__main__":
    unittest.main()
