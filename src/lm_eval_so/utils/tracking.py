from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional, Generator
from contextlib import contextmanager

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


class PipelineContext:
    """
    Manages MLflow runs for a pipeline.
    
    Usage:
        with PipelineContext("experiment_name") as ctx:
            ctx.log_params(...)
            with ctx.step("step1"):
                 ...
    """
    
    def __init__(self, experiment_name: str, base_output_dir: str = "pipeline_outputs"):
        self.experiment_name = experiment_name
        self.base_output_dir = base_output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(base_output_dir, f"run_{self.timestamp}")
        self._parent_run = None
        
    def __enter__(self) -> "PipelineContext":
        if not MLFLOW_AVAILABLE:
            print("Warning: MLflow not available. Tracking disabled.")
            return self
            
        os.makedirs(self.run_dir, exist_ok=True)
        mlflow.set_experiment(self.experiment_name)
        
        # Start Parent Run
        self._parent_run = mlflow.start_run(run_name=f"pipeline_{self.timestamp}")
        print(f"🚀 Started Pipeline Run: {self._parent_run.info.run_id}")
        
        mlflow.log_params({
            "pipeline_timestamp": self.timestamp,
            "output_dir": self.run_dir
        })
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if MLFLOW_AVAILABLE and self._parent_run:
            if exc_type:
                mlflow.set_tag("status", "failed")
                print(f"❌ Pipeline Failed: {exc_val}")
            else:
                mlflow.set_tag("status", "completed")
                print("✅ Pipeline Completed")
            mlflow.end_run()

    @contextmanager
    def step(self, step_name: str) -> Generator[str, None, None]:
        """
        Creates a nested run for a step.
        Returns the output directory for this step.
        """
        step_dir = os.path.join(self.run_dir, step_name)
        os.makedirs(step_dir, exist_ok=True)
        
        print(f"\n[Step] {step_name}")
        
        if MLFLOW_AVAILABLE and mlflow.active_run():
            with mlflow.start_run(run_name=step_name, nested=True) as child_run:
                yield step_dir
        else:
             yield step_dir

    def log_params(self, params: Dict[str, Any]):
        if MLFLOW_AVAILABLE and mlflow.active_run():
            mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float]):
        if MLFLOW_AVAILABLE and mlflow.active_run():
            mlflow.log_metrics(metrics)
            
    def log_artifact(self, local_path: str):
        if MLFLOW_AVAILABLE and mlflow.active_run():
            mlflow.log_artifact(local_path)
