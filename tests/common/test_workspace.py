import shutil
from pathlib import Path
import pytest
from chatbot_tester.common.workspace import Workspace

@pytest.fixture
def temp_workspace(tmp_path):
    ws_path = tmp_path / "test_ws"
    ws = Workspace(ws_path)
    yield ws
    # Cleanup handled by tmp_path fixture usually, but explicitly is fine too
    if ws_path.exists():
        shutil.rmtree(ws_path)

def test_workspace_initialization(temp_workspace):
    assert isinstance(temp_workspace.root, Path)
    assert temp_workspace.root.name == "test_ws"

def test_create_run_auto_id(temp_workspace):
    run_id, run_path = temp_workspace.create_run()

    assert run_path.exists()
    assert run_path.is_dir()
    assert run_path.name == run_id
    assert run_path.parent == temp_workspace.runs_dir

def test_create_run_manual_id(temp_workspace):
    run_id = "my_custom_run"
    returned_id, run_path = temp_workspace.create_run(run_id)

    assert returned_id == run_id
    assert run_path.exists()
    assert run_path.name == "my_custom_run"

def test_create_run_duplicate_error(temp_workspace):
    run_id = "duplicate_run"
    temp_workspace.create_run(run_id)

    with pytest.raises(FileExistsError):
        temp_workspace.create_run(run_id)

def test_validate_id_invalid_chars(temp_workspace):
    with pytest.raises(ValueError):
        temp_workspace.create_run("invalid/id")

    with pytest.raises(ValueError):
        temp_workspace.get_run_dir("invalid space")

def test_get_run_dir(temp_workspace):
    run_id = "test_run"
    path = temp_workspace.get_run_dir(run_id, ensure_exists=True)

    assert path.exists()
    assert path == temp_workspace.runs_dir / run_id

def test_get_dataset_dir(temp_workspace):
    ds_id = "test_dataset"
    path = temp_workspace.get_dataset_dir(ds_id, ensure_exists=True)

    assert path.exists()
    assert path == temp_workspace.datasets_dir / ds_id
