"""Runtime tests for doctor interpreter diagnostics on Windows bootstrap paths."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import claude_code.main as main_mod


def test_interpreter_path_classification_detects_windowsapps_stub():
    stub_path = r"C:\Users\demo\AppData\Local\Microsoft\WindowsApps\python.exe"
    assert main_mod._classify_interpreter_path(stub_path, platform_name="win32") == "windowsapps_stub"
    assert main_mod._is_windowsapps_stub(stub_path, platform_name="win32") is True


def test_collect_interpreter_diagnostics_windowsapps_stub_regression():
    diagnostics = main_mod._collect_interpreter_diagnostics(
        platform_name="win32",
        executable_path=r"C:\Program Files\Python311\python.exe",
        python_on_path=r"C:\Users\demo\AppData\Local\Microsoft\WindowsApps\python.exe",
    )

    assert diagnostics.python_on_path_source == "windowsapps_stub"
    assert diagnostics.has_windowsapps_stub_risk is True
    assert diagnostics.warning is not None
    assert "WindowsApps python.exe stub detected" in diagnostics.warning
    assert "py -3 -m claude_code.main" in diagnostics.recommended_launcher


def test_collect_interpreter_diagnostics_virtualenv_has_no_stub_risk():
    diagnostics = main_mod._collect_interpreter_diagnostics(
        platform_name="win32",
        executable_path=r"D:\repo\.venv\Scripts\python.exe",
        python_on_path=r"D:\repo\.venv\Scripts\python.exe",
    )

    assert diagnostics.executable_source == "virtualenv"
    assert diagnostics.python_on_path_source == "virtualenv"
    assert diagnostics.has_windowsapps_stub_risk is False
    assert diagnostics.warning is None


class _FakeTable:
    last_instance = None

    def __init__(self, *args, **kwargs):
        self.rows: list[tuple[str, str, str]] = []
        _FakeTable.last_instance = self

    def add_column(self, *args, **kwargs):
        return None

    def add_row(self, *args):
        self.rows.append(tuple(str(item) for item in args))


class _FakeConsole:
    last_instance = None

    def __init__(self, *args, **kwargs):
        self.printed: list[object] = []
        _FakeConsole.last_instance = self

    def print(self, obj):
        self.printed.append(obj)


@pytest.mark.asyncio
async def test_run_doctor_outputs_warn_branch_for_stub_risk(monkeypatch):
    import rich.console as rich_console
    import rich.table as rich_table

    monkeypatch.setattr(rich_console, "Console", _FakeConsole)
    monkeypatch.setattr(rich_table, "Table", _FakeTable)
    monkeypatch.setattr(
        main_mod,
        "_collect_interpreter_diagnostics",
        lambda: main_mod.InterpreterDiagnostics(
            executable=r"C:\Python311\python.exe",
            python_on_path=r"C:\Users\demo\AppData\Local\Microsoft\WindowsApps\python.exe",
            executable_source="system",
            python_on_path_source="windowsapps_stub",
            has_windowsapps_stub_risk=True,
            warning="WindowsApps python.exe stub detected in python on PATH.",
            recommended_launcher="Use `py -3 -m claude_code.main`.",
        ),
    )
    monkeypatch.setattr(main_mod, "ContextBuilder", lambda cwd: SimpleNamespace(get_system_context=lambda: {"gitStatus": "ok"}))
    monkeypatch.setattr(main_mod, "create_runtime", lambda working_dir=None: SimpleNamespace(query_engine=object()))
    monkeypatch.setattr(main_mod.os, "getcwd", lambda: "D:/workspace")
    monkeypatch.setattr(main_mod.sys, "platform", "win32")

    await main_mod.run_doctor()

    rows = _FakeTable.last_instance.rows
    assert any(row[0] == "Interpreter" and row[1] == "WARN" for row in rows)
    assert any(row[0] == "Interpreter Risk" and row[1] == "WARN" for row in rows)
    assert any(row[0] == "Windows Launcher" and row[1] == "INFO" for row in rows)


@pytest.mark.asyncio
async def test_run_doctor_outputs_ok_branch_without_stub_risk(monkeypatch):
    import rich.console as rich_console
    import rich.table as rich_table

    monkeypatch.setattr(rich_console, "Console", _FakeConsole)
    monkeypatch.setattr(rich_table, "Table", _FakeTable)
    monkeypatch.setattr(
        main_mod,
        "_collect_interpreter_diagnostics",
        lambda: main_mod.InterpreterDiagnostics(
            executable="/usr/bin/python3",
            python_on_path="/usr/bin/python3",
            executable_source="system",
            python_on_path_source="system",
            has_windowsapps_stub_risk=False,
            warning=None,
            recommended_launcher="Use `python -m claude_code.main`.",
        ),
    )
    monkeypatch.setattr(main_mod, "ContextBuilder", lambda cwd: SimpleNamespace(get_system_context=lambda: {"gitStatus": "ok"}))
    monkeypatch.setattr(main_mod, "create_runtime", lambda working_dir=None: SimpleNamespace(query_engine=object()))
    monkeypatch.setattr(main_mod.os, "getcwd", lambda: "/workspace")
    monkeypatch.setattr(main_mod.sys, "platform", "linux")

    await main_mod.run_doctor()

    rows = _FakeTable.last_instance.rows
    assert any(row[0] == "Interpreter" and row[1] == "OK" for row in rows)
    assert not any(row[0] == "Interpreter Risk" for row in rows)
    assert not any(row[0] == "Windows Launcher" for row in rows)
