import json
import stat
from pathlib import Path

import pytest

import home_ai_cluster.retained_configuration as retained_configuration
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedConfigurationError,
    RetainedLocalConfiguration,
    load_retained_configuration,
    remove_retained_configuration,
    retained_configuration_file,
    save_retained_configuration,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration


def ollama_configuration(
    *, capabilities: tuple[str, ...] | None = None
) -> RetainedConfiguration:
    return RetainedConfiguration(
        local=RetainedLocalConfiguration(
            runtime=LocalRuntimeCompositionValues(
                runtime="ollama",
                ollama_model="private-model",
                ollama_disable_thinking=True,
            ),
            local_capabilities=capabilities,
        )
    )


def test_path_uses_xdg_config_home_without_creating_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("HOME", "/not-the-real-home")

    assert retained_configuration_file() == (
        tmp_path / "home-ai-cluster" / "retained-config.json"
    )
    assert not (tmp_path / "home-ai-cluster").exists()


def test_path_uses_home_config_fallback_when_xdg_config_home_is_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert retained_configuration_file() == (
        tmp_path / ".config" / "home-ai-cluster" / "retained-config.json"
    )


@pytest.mark.parametrize("xdg_config_home", ["", "relative-config"])
def test_path_uses_home_config_fallback_when_xdg_config_home_is_not_absolute(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    xdg_config_home: str,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", xdg_config_home)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert retained_configuration_file() == (
        tmp_path / ".config" / "home-ai-cluster" / "retained-config.json"
    )
    assert not (tmp_path / ".config").exists()


def test_path_uses_macos_application_support_without_creating_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(retained_configuration.sys, "platform", "darwin")
    monkeypatch.setattr(retained_configuration.Path, "home", lambda: tmp_path)

    assert retained_configuration_file() == (
        tmp_path
        / "Library"
        / "Application Support"
        / "home-ai-cluster"
        / "retained-config.json"
    )
    assert not (tmp_path / "Library").exists()


def test_path_uses_windows_local_app_data_without_creating_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    local_app_data = tmp_path / "LocalAppData"
    monkeypatch.setattr(retained_configuration.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    assert retained_configuration_file() == (
        local_app_data / "home-ai-cluster" / "retained-config.json"
    )
    assert not local_app_data.exists()


@pytest.mark.parametrize("local_app_data", [None, "", "relative-local-app-data"])
def test_windows_path_falls_back_to_home_local_app_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    local_app_data: str | None,
) -> None:
    monkeypatch.setattr(retained_configuration.sys, "platform", "win32")
    monkeypatch.setattr(retained_configuration.Path, "home", lambda: tmp_path)
    if local_app_data is None:
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
    else:
        monkeypatch.setenv("LOCALAPPDATA", local_app_data)

    assert retained_configuration_file() == (
        tmp_path / "AppData" / "Local" / "home-ai-cluster" / "retained-config.json"
    )
    assert not (tmp_path / "AppData").exists()


def test_save_creates_owner_only_application_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_home = tmp_path / "config-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    path = retained_configuration_file()

    save_retained_configuration(RetainedConfiguration())

    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_does_not_chmod_an_existing_application_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_home = tmp_path / "config-home"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    path = retained_configuration_file()
    path.parent.mkdir(parents=True)
    path.parent.chmod(0o755)

    save_retained_configuration(RetainedConfiguration())

    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o755


def test_missing_file_loads_empty_configuration(tmp_path: Path) -> None:
    assert load_retained_configuration(tmp_path / "missing.json") == (
        RetainedConfiguration()
    )


def test_remove_retained_configuration_removes_only_the_configuration_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "home-ai-cluster" / "retained-config.json"
    unrelated = path.parent / "unrelated.txt"
    path.parent.mkdir()
    path.write_text("malformed", encoding="utf-8")
    unrelated.write_text("preserve", encoding="utf-8")

    remove_retained_configuration(path)

    assert not path.exists()
    assert unrelated.read_text(encoding="utf-8") == "preserve"


def test_remove_retained_configuration_is_idempotent_without_creating_parent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing" / "retained-config.json"

    remove_retained_configuration(path)

    assert not path.parent.exists()


def test_remove_retained_configuration_bounds_os_errors_without_path_leakage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "private" / "retained-config.json"

    def fail_unlink(_path: Path) -> None:
        raise OSError("private removal failure")

    monkeypatch.setattr(retained_configuration.Path, "unlink", fail_unlink)

    with pytest.raises(RetainedConfigurationError) as raised:
        remove_retained_configuration(path)

    assert str(raised.value) == "unable to remove retained configuration"
    assert str(path) not in str(raised.value)
    assert "private removal failure" not in str(raised.value)


def test_chat_external_information_fallback_defaults_to_not_authorized() -> None:
    assert RetainedConfiguration().chat_external_information_fallback is False


def test_chat_external_information_fallback_round_trips_as_json_boolean(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        chat_external_information_fallback=True,
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration
    assert (
        json.loads(path.read_text(encoding="utf-8"))[
            "chat_external_information_fallback"
        ]
        is True
    )


def test_chat_external_information_fallback_coexists_with_other_retained_facts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        local=ollama_configuration().local,
        remote_nodes=(
            RemoteNodeDeclaration("remote", "http://192.0.2.1:25042", ("chat",)),
        ),
        external_information_plugin="searxng",
        chat_external_information_fallback=True,
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration


@pytest.mark.parametrize("value", ["true", 1, None])
def test_non_boolean_chat_external_information_fallback_is_rejected(
    tmp_path: Path, value: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(
        json.dumps(
            {
                "local": None,
                "remote_nodes": [],
                "external_information_plugin": None,
                "chat_external_information_fallback": value,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)


def test_non_boolean_chat_external_information_fallback_is_rejected_on_save(
    tmp_path: Path,
) -> None:
    with pytest.raises(RetainedConfigurationError):
        save_retained_configuration(
            RetainedConfiguration(
                chat_external_information_fallback=1,  # type: ignore[arg-type]
            ),
            tmp_path / "retained.json",
        )


def test_external_information_plugin_round_trips_exactly(tmp_path: Path) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(external_information_plugin="tävily")

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["external_information_plugin"] == "tävily"


def test_external_information_plugin_coexists_with_local_and_remote_facts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        local=ollama_configuration().local,
        remote_nodes=(
            RemoteNodeDeclaration("remote", "http://192.0.2.1:25042", ("chat",)),
        ),
        external_information_plugin="searxng",
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration


@pytest.mark.parametrize("plugin", ["", "   ", "x" * 65])
def test_invalid_external_information_plugin_is_rejected_on_save(
    tmp_path: Path, plugin: str
) -> None:
    with pytest.raises(RetainedConfigurationError):
        save_retained_configuration(
            RetainedConfiguration(external_information_plugin=plugin),
            tmp_path / "retained.json",
        )


def test_non_string_external_information_plugin_is_rejected_on_save(
    tmp_path: Path,
) -> None:
    with pytest.raises(RetainedConfigurationError):
        save_retained_configuration(
            RetainedConfiguration(external_information_plugin=42),  # type: ignore[arg-type]
            tmp_path / "retained.json",
        )


@pytest.mark.parametrize("plugin", [42, "", "\t", "x" * 65])
def test_invalid_serialized_external_information_plugin_is_rejected(
    tmp_path: Path, plugin: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(
        json.dumps(
            {
                "local": None,
                "remote_nodes": [],
                "external_information_plugin": plugin,
                "chat_external_information_fallback": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)


def test_ollama_and_local_capability_values_round_trip_distinctly(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    configuration = ollama_configuration(capabilities=("code", "chat"))

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["local"]["ollama_disable_thinking"] is True
    assert document["local"]["local_capabilities"] == ["code", "chat"]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_none_local_capabilities_round_trips_without_inventing_a_default(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"

    save_retained_configuration(ollama_configuration(), path)

    assert load_retained_configuration(path).local is not None
    assert load_retained_configuration(path).local.local_capabilities is None


def test_legacy_local_shape_loads_without_execution_limit_or_rewrite(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    document = {
        "local": {
            "runtime": "ollama",
            "ollama_model": None,
            "ollama_disable_thinking": False,
            "llama_server_base_url": None,
            "llama_server_model": None,
            "local_capabilities": None,
        },
        "remote_nodes": [],
        "external_information_plugin": None,
        "chat_external_information_fallback": False,
    }
    path.write_text(json.dumps(document), encoding="utf-8")
    before = path.read_bytes()

    configuration = load_retained_configuration(path)

    assert configuration.local is not None
    assert configuration.local.execution_limit is None
    assert path.read_bytes() == before


def test_local_execution_limit_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        local=RetainedLocalConfiguration(
            runtime=LocalRuntimeCompositionValues(runtime="ollama"),
            execution_limit=2,
        )
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration
    assert json.loads(path.read_text(encoding="utf-8"))["local"]["execution_limit"] == 2


@pytest.mark.parametrize("value", [0, -1, "2", True, None])
def test_invalid_retained_local_execution_limit_is_rejected(
    tmp_path: Path, value: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(
        json.dumps(
            {
                "local": {
                    "runtime": "ollama",
                    "ollama_model": None,
                    "ollama_disable_thinking": False,
                    "llama_server_base_url": None,
                    "llama_server_model": None,
                    "local_capabilities": None,
                    "execution_limit": value,
                },
                "remote_nodes": [],
                "external_information_plugin": None,
                "chat_external_information_fallback": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)


def test_llama_server_round_trip_preserves_existing_url_normalization(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        local=RetainedLocalConfiguration(
            runtime=LocalRuntimeCompositionValues(
                runtime="llama-server",
                llama_server_base_url="http://127.0.0.1:8080/",
                llama_server_model="private-model",
            )
        )
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path).local == RetainedLocalConfiguration(
        runtime=LocalRuntimeCompositionValues(
            runtime="llama-server",
            llama_server_base_url="http://127.0.0.1:8080",
            llama_server_model="private-model",
        )
    )


def test_ordered_remote_nodes_and_capabilities_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        remote_nodes=(
            RemoteNodeDeclaration(
                "remote-a", "https://remote-a.example:8000", ("code",)
            ),
            RemoteNodeDeclaration(
                "remote-b", "http://192.0.2.20:25042", ("summarize", "chat")
            ),
        )
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration


def test_save_uses_same_directory_temporary_replacement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "retained.json"
    replacements: list[tuple[object, object]] = []
    replace = retained_configuration.os.replace

    def record_replace(source: object, target: object) -> None:
        replacements.append((source, target))
        replace(source, target)

    monkeypatch.setattr(retained_configuration.os, "replace", record_replace)

    save_retained_configuration(RetainedConfiguration(), path)

    assert len(replacements) == 1
    assert Path(replacements[0][0]).parent == path.parent
    assert replacements[0][1] == path


@pytest.mark.parametrize(
    "contents",
    [b"not json", b"\xff"],
)
def test_invalid_encoding_or_json_fails_without_echoing_contents(
    tmp_path: Path, contents: bytes
) -> None:
    path = tmp_path / "private-path.json"
    path.write_bytes(contents)

    with pytest.raises(RetainedConfigurationError) as raised:
        load_retained_configuration(path)

    assert str(raised.value) == "invalid retained configuration"
    assert "private-path" not in str(raised.value)
    assert "not json" not in str(raised.value)


def test_rfc_0094_era_document_loads_with_later_defaults_without_rewriting(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    contents = b'{"local":null,"remote_nodes":[]}\n'
    path.write_bytes(contents)

    assert load_retained_configuration(path) == RetainedConfiguration()
    assert path.read_bytes() == contents


def test_rfc_0095_era_document_loads_with_chat_default_without_rewriting(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    contents = (
        b'{"local":null,"remote_nodes":[],"external_information_plugin":"searxng"}\n'
    )
    path.write_bytes(contents)

    assert load_retained_configuration(path) == RetainedConfiguration(
        external_information_plugin="searxng"
    )
    assert path.read_bytes() == contents


def test_current_document_still_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        external_information_plugin="searxng",
        chat_external_information_fallback=True,
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration


@pytest.mark.parametrize(
    "document",
    [
        {"remote_nodes": []},
        {"local": None},
        {
            "local": None,
            "remote_nodes": [],
            "unexpected": True,
        },
    ],
)
def test_original_fields_remain_required_and_unknown_top_level_fields_fail(
    tmp_path: Path, document: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)


@pytest.mark.parametrize(
    "document",
    [
        {
            "local": None,
            "remote_nodes": [],
            "external_information_plugin": "",
        },
        {
            "local": None,
            "remote_nodes": [],
            "external_information_plugin": None,
            "chat_external_information_fallback": "false",
        },
    ],
)
def test_present_optional_fields_remain_strictly_validated(
    tmp_path: Path, document: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)


@pytest.mark.parametrize(
    "document",
    [
        {"local": None},
        {
            "local": None,
            "remote_nodes": [],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
            "unexpected": True,
        },
        {
            "local": {"unexpected": True},
            "remote_nodes": [],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        },
        {
            "local": None,
            "remote_nodes": [
                {
                    "node_id": "remote",
                    "base_url": "http://192.0.2.1:25042",
                    "capabilities": ["chat"],
                    "unexpected": True,
                }
            ],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        },
    ],
)
def test_unknown_or_missing_structural_fields_fail(
    tmp_path: Path, document: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)


@pytest.mark.parametrize(
    "document",
    [
        {
            "local": {
                "runtime": "llama-server",
                "ollama_model": "private-model",
                "ollama_disable_thinking": False,
                "llama_server_base_url": "http://127.0.0.1:8080",
                "llama_server_model": "private-model",
                "local_capabilities": None,
            },
            "remote_nodes": [],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        },
        {
            "local": {
                "runtime": "ollama",
                "ollama_model": None,
                "ollama_disable_thinking": False,
                "llama_server_base_url": None,
                "llama_server_model": None,
                "local_capabilities": [],
            },
            "remote_nodes": [],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        },
        {
            "local": None,
            "remote_nodes": [
                {
                    "node_id": "local",
                    "base_url": "http://private.example:25042",
                    "capabilities": ["chat"],
                }
            ],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        },
        {
            "local": None,
            "remote_nodes": [
                {
                    "node_id": "remote",
                    "base_url": "http://private.example:25042/path",
                    "capabilities": ["unknown"],
                }
            ],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        },
    ],
)
def test_invalid_semantic_values_fail_without_echoing_private_values(
    tmp_path: Path, document: object
) -> None:
    path = tmp_path / "retained.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(RetainedConfigurationError) as raised:
        load_retained_configuration(path)

    assert "private.example" not in str(raised.value)
    assert "private-model" not in str(raised.value)


@pytest.mark.parametrize("field", ["node_id", "base_url"])
def test_duplicate_remote_values_fail_explicitly(tmp_path: Path, field: str) -> None:
    path = tmp_path / "retained.json"
    first = {
        "node_id": "remote-a",
        "base_url": "http://192.0.2.1:25042",
        "capabilities": ["chat"],
    }
    second = {
        "node_id": "remote-b",
        "base_url": "http://192.0.2.2:25042",
        "capabilities": ["summarize"],
    }
    second[field] = first[field]

    contents = json.dumps(
        {
            "local": None,
            "remote_nodes": [first, second],
            "external_information_plugin": None,
            "chat_external_information_fallback": False,
        }
    )
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(RetainedConfigurationError):
        load_retained_configuration(path)
    assert path.read_text(encoding="utf-8") == contents


def test_invalid_state_does_not_replace_an_existing_destination(tmp_path: Path) -> None:
    path = tmp_path / "retained.json"
    original = b'{"local":null,"remote_nodes":[]}\n'
    path.write_bytes(original)
    invalid = RetainedConfiguration(
        local=RetainedLocalConfiguration(
            runtime=LocalRuntimeCompositionValues(
                runtime="llama-server",
                ollama_model="private-model",
                llama_server_base_url="http://127.0.0.1:8080",
                llama_server_model="private-model",
            )
        )
    )

    with pytest.raises(RetainedConfigurationError):
        save_retained_configuration(invalid, path)

    assert path.read_bytes() == original


def test_failed_replacement_cleans_up_temporary_file_and_preserves_destination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "retained.json"
    original = b'{"local":null,"remote_nodes":[]}\n'
    path.write_bytes(original)

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("private replacement failure")

    monkeypatch.setattr(retained_configuration.os, "replace", fail_replace)

    with pytest.raises(RetainedConfigurationError) as raised:
        save_retained_configuration(ollama_configuration(), path)

    assert str(raised.value) == "unable to save retained configuration"
    assert path.read_bytes() == original
    assert not list(tmp_path.glob(".retained-config-*"))
