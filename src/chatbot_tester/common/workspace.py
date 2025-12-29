import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class Workspace:
    """
    Manages the directory structure for experiments, including runs and datasets.

    Structure:
        root/
            runs/
                <run_id>/
            datasets/
                <dataset_id>/
    """

    def __init__(self, root: str | Path = "./workspace"):
        self._root = Path(root).resolve()

    @property
    def root(self) -> Path:
        """Returns the absolute path to the workspace root."""
        return self._root

    @property
    def runs_dir(self) -> Path:
        """Returns the path to the runs directory."""
        return self._root / "runs"

    @property
    def datasets_dir(self) -> Path:
        """Returns the path to the datasets directory."""
        return self._root / "datasets"

    def _ensure_dir(self, path: Path) -> Path:
        """Ensures the directory exists."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _validate_id(self, name: str) -> None:
        """Validates that the ID is safe for file systems."""
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", name):
            raise ValueError(f"Invalid ID '{name}': must contain only alphanumeric characters, underscores, hyphens, or dots.")

    def create_run(self, run_id: Optional[str] = None) -> Tuple[str, Path]:
        """
        Creates a new run directory.

        Args:
            run_id: Optional identifier. If not provided, one will be generated based on timestamp and UUID.

        Returns:
            A tuple containing the run_id and the path to the run directory.
        """
        if run_id is None:
            # Generate a run ID: YYYYMMDD_HHMMSS_shortuuid
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            run_id = f"{timestamp}_{short_uuid}"

        self._validate_id(run_id)

        run_path = self.runs_dir / run_id
        if run_path.exists():
            raise FileExistsError(f"Run directory already exists: {run_path}")

        self._ensure_dir(run_path)
        return run_id, run_path

    def get_run_dir(self, run_id: str, ensure_exists: bool = False) -> Path:
        """
        Gets the path for a run.

        Args:
            run_id: The run identifier.
            ensure_exists: If True, creates the directory if it doesn't exist.

        Returns:
            The path to the run directory.
        """
        self._validate_id(run_id)
        run_path = self.runs_dir / run_id

        if ensure_exists:
            self._ensure_dir(run_path)

        return run_path

    def get_dataset_dir(self, dataset_id: str, ensure_exists: bool = False) -> Path:
        """
        Gets the path for a dataset.

        Args:
            dataset_id: The dataset identifier.
            ensure_exists: If True, creates the directory if it doesn't exist.

        Returns:
            The path to the dataset directory.
        """
        self._validate_id(dataset_id)
        dataset_path = self.datasets_dir / dataset_id

        if ensure_exists:
            self._ensure_dir(dataset_path)

        return dataset_path
