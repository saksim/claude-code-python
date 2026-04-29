"""Runtime tests for main entry helpers."""

from __future__ import annotations

import pytest

import claude_code.main as main_mod
from claude_code.permissions import PermissionMode


class _AssistantMessage:
    def __init__(self, content):
        self.role = "assistant"
        self.content = content


class _FakeEngine:
    async def query(self, query: str):
        yield {"type": "text", "content": "stream-"}
        yield _AssistantMessage([{"type": "text", "text": "final"}])


@pytest.mark.asyncio
async def test_run_single_query_prints_stream_and_final_text(monkeypatch, capsys):
    monkeypatch.setattr(
        main_mod,
        "create_engine",
        lambda model=None, working_dir=None: _FakeEngine(),
    )

    code = await main_mod.run_single_query("hello")

    out = capsys.readouterr().out
    assert code == 0
    assert "stream-final" in out


def test_setup_api_client_openai_requires_api_key(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError):
        main_mod.setup_api_client()


def test_setup_api_client_ollama_allows_dummy_key(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "ollama")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured = {}

    class _FakeApiClient:
        def __init__(self, config):
            captured["config"] = config

    monkeypatch.setattr(main_mod, "APIClient", _FakeApiClient)

    client = main_mod.setup_api_client()

    assert isinstance(client, _FakeApiClient)
    assert captured["config"].provider.value == "openai"
    assert captured["config"].api_key == "dummy"
    assert captured["config"].base_url == "http://localhost:11434/v1"


def test_setup_api_client_accepts_config_provider_without_env(monkeypatch):
    monkeypatch.delenv("CLAUDE_API_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured = {}

    class _FakeApiClient:
        def __init__(self, config):
            captured["config"] = config

    monkeypatch.setattr(main_mod, "APIClient", _FakeApiClient)
    config = main_mod.Config(
        api_provider="ollama",
        openai_base_url="http://localhost:11434/v1",
    )

    client = main_mod.setup_api_client(config)

    assert isinstance(client, _FakeApiClient)
    assert captured["config"].provider.value == "openai"
    assert captured["config"].api_key == "dummy"


def test_setup_api_client_prefers_env_api_key_over_config_for_anthropic(monkeypatch):
    monkeypatch.delenv("CLAUDE_API_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-1234")

    captured = {}

    class _FakeApiClient:
        def __init__(self, config):
            captured["config"] = config

    monkeypatch.setattr(main_mod, "APIClient", _FakeApiClient)
    config = main_mod.Config(api_provider="anthropic", api_key="sk-ant-config-0000")

    client = main_mod.setup_api_client(config)

    assert isinstance(client, _FakeApiClient)
    assert captured["config"].provider.value == "anthropic"
    assert captured["config"].api_key == "sk-ant-env-1234"


def test_setup_api_client_uses_openai_config_key_when_env_missing(monkeypatch):
    monkeypatch.delenv("CLAUDE_API_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured = {}

    class _FakeApiClient:
        def __init__(self, config):
            captured["config"] = config

    monkeypatch.setattr(main_mod, "APIClient", _FakeApiClient)
    config = main_mod.Config(
        api_provider="openai",
        api_key="sk-openai-config-5678",
        openai_base_url="https://api.example.invalid/v1",
    )

    client = main_mod.setup_api_client(config)

    assert isinstance(client, _FakeApiClient)
    assert captured["config"].provider.value == "openai"
    assert captured["config"].api_key == "sk-openai-config-5678"
    assert captured["config"].base_url == "https://api.example.invalid/v1"


def test_create_engine_uses_model_from_config_when_arg_missing(monkeypatch):
    captured = {}

    class _FakeQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            captured["config"] = config

    cfg = main_mod.Config(
        model="claude-haiku-20240307",
        permission_mode=PermissionMode.DEFAULT,
    )

    monkeypatch.setattr(main_mod, "get_config", lambda: cfg)
    monkeypatch.setattr(main_mod, "setup_api_client", lambda app_config=None: object())
    monkeypatch.setattr(main_mod, "create_default_registry", lambda: object())
    monkeypatch.setattr(main_mod, "QueryEngine", _FakeQueryEngine)

    main_mod.create_engine()

    assert captured["config"].model == "claude-haiku-20240307"


def test_create_runtime_attaches_runtime_services(monkeypatch):
    class _FakeSession:
        def __init__(self):
            self.id = "session-123"
            self.metadata = type(
                "_Metadata",
                (),
                {"working_directory": "D:/initial", "model": "claude-initial"},
            )()

    class _FakeSessionManager:
        @classmethod
        def from_store(cls, store):
            return cls()

        def ensure_current_session(self):
            return _FakeSession()

    class _FakeQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            self.api_client = api_client
            self.config = config
            self.tool_registry = tool_registry

    fake_api_client = object()
    fake_registry = object()
    fake_history = object()
    fake_task_manager = object()
    fake_hooks = object()
    fake_memory = object()
    fake_event_journal = object()
    fake_session_store = object()
    fake_app = object()

    monkeypatch.setattr(main_mod, "get_config", lambda: main_mod.Config(model="claude-test-model"))
    monkeypatch.setattr(main_mod, "setup_api_client", lambda app_config=None: fake_api_client)
    monkeypatch.setattr(main_mod, "create_default_registry", lambda: fake_registry)
    monkeypatch.setattr(main_mod, "QueryEngine", _FakeQueryEngine)
    monkeypatch.setattr(main_mod, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(main_mod, "SQLiteSessionStore", lambda db_path=None: fake_session_store)
    monkeypatch.setattr(main_mod, "HistoryManager", lambda storage_path=None: fake_history)
    monkeypatch.setattr(main_mod, "SQLiteEventJournal", lambda db_path=None: fake_event_journal)
    monkeypatch.setattr(
        main_mod,
        "create_task_manager_with_event_journal",
        lambda config, event_journal: fake_task_manager,
    )
    monkeypatch.setattr(main_mod, "HooksManager", lambda config_path=None: fake_hooks)
    monkeypatch.setattr(main_mod, "get_memory", lambda: fake_memory)
    monkeypatch.setattr(main_mod, "_create_application", lambda app_config: fake_app)

    runtime = main_mod.create_runtime(model="claude-custom-model", working_dir="D:/runtime")

    assert runtime.query_engine.config.model == "claude-custom-model"
    assert runtime.query_engine.config.working_directory == "D:/runtime"
    assert runtime.query_engine.config.session_id == "session-123"
    assert runtime.query_engine.session_manager is runtime.session_manager
    assert runtime.query_engine.history_manager is runtime.history_manager
    assert runtime.query_engine.task_manager is runtime.task_manager
    assert runtime.query_engine.hooks_manager is runtime.hooks_manager
    assert runtime.query_engine.memory is runtime.memory
    assert runtime.query_engine.event_journal is runtime.event_journal


def test_create_engine_delegates_to_runtime_context(monkeypatch):
    fake_engine = object()
    fake_runtime = main_mod.RuntimeContext(
        application=object(),
        app_config=main_mod.Config(),
        api_client=object(),
        tool_registry=object(),
        query_engine=fake_engine,
        session_manager=object(),
        history_manager=object(),
        task_manager=object(),
        hooks_manager=object(),
        memory=object(),
        event_journal=object(),
        working_directory="D:/cwd",
    )
    monkeypatch.setattr(main_mod, "create_runtime", lambda model=None, working_dir=None: fake_runtime)

    engine = main_mod.create_engine(model="claude-model", working_dir="D:/cwd")

    assert engine is fake_engine


def test_main_mcp_serve_uses_runtime_registry(monkeypatch):
    import claude_code.mcp.server as mcp_server_mod

    captured = {}

    async def _fake_run_mcp_server(working_directory: str, server_name: str, tool_registry=None):
        captured["working_directory"] = working_directory
        captured["server_name"] = server_name
        captured["tool_registry"] = tool_registry

    fake_registry = object()
    fake_runtime = main_mod.RuntimeContext(
        application=object(),
        app_config=main_mod.Config(),
        api_client=object(),
        tool_registry=fake_registry,
        query_engine=object(),
        session_manager=object(),
        history_manager=object(),
        task_manager=object(),
        hooks_manager=object(),
        memory=object(),
        event_journal=object(),
        working_directory="D:/cwd",
    )

    monkeypatch.setattr(main_mod, "create_runtime", lambda model=None, working_dir=None: fake_runtime)
    monkeypatch.setattr(mcp_server_mod, "run_mcp_server", _fake_run_mcp_server)
    monkeypatch.setattr(
        main_mod,
        "setup_default_commands",
        lambda: (_ for _ in ()).throw(AssertionError("should not reach command setup in --mcp-serve mode")),
    )
    monkeypatch.setattr(main_mod.sys, "argv", ["claude-code", "--mcp-serve", "--mcp-name", "runtime-test"])

    main_mod.main()

    assert captured["server_name"] == "runtime-test"
    assert captured["tool_registry"] is fake_registry


def test_main_daemon_serve_uses_runtime_context(monkeypatch):
    import claude_code.server.control_plane as control_plane_mod

    captured = {}
    fake_runtime = main_mod.RuntimeContext(
        application=object(),
        app_config=main_mod.Config(),
        api_client=object(),
        tool_registry=object(),
        query_engine=object(),
        session_manager=object(),
        history_manager=object(),
        task_manager=object(),
        hooks_manager=object(),
        memory=object(),
        event_journal=object(),
        working_directory="D:/cwd",
    )

    def _fake_run_control_plane_daemon(runtime, *, host, port, request_timeout_seconds):
        captured["runtime"] = runtime
        captured["host"] = host
        captured["port"] = port
        captured["request_timeout_seconds"] = request_timeout_seconds

    monkeypatch.setattr(main_mod, "create_runtime", lambda model=None, working_dir=None: fake_runtime)
    monkeypatch.setattr(control_plane_mod, "run_control_plane_daemon", _fake_run_control_plane_daemon)
    monkeypatch.setattr(
        main_mod,
        "setup_default_commands",
        lambda: (_ for _ in ()).throw(AssertionError("should not reach command setup in --daemon-serve mode")),
    )
    monkeypatch.setattr(
        main_mod.sys,
        "argv",
        [
            "claude-code",
            "--daemon-serve",
            "--daemon-host",
            "127.0.0.2",
            "--daemon-port",
            "9011",
            "--daemon-timeout",
            "8.5",
        ],
    )

    main_mod.main()

    assert captured["runtime"] is fake_runtime
    assert captured["host"] == "127.0.0.2"
    assert captured["port"] == 9011
    assert captured["request_timeout_seconds"] == 8.5


def test_config_accepts_local_openai_compatible_providers():
    assert main_mod.Config(api_provider="ollama").api_provider == "ollama"
    assert main_mod.Config(api_provider="vllm").api_provider == "vllm"
    assert main_mod.Config(api_provider="deepseek").api_provider == "deepseek"
