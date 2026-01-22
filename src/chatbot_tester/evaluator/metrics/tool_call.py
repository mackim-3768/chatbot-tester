from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from ..base import Metric
from ..domain import EvalScore, RunRecord, TestSampleRecord


class ToolCallMatchMetric(Metric):
    """
    Evaluates whether the predicted text contains a JSON list of tool calls 
    that matches the expected tool calls.
    """

    def __init__(
        self,
        *,
        exclude_args: Optional[List[str]] = None,
        allow_order_mismatch: bool = False,
        **kwargs: Any
    ):
        super().__init__(name="tool_call_match", **kwargs)
        self.exclude_args = exclude_args or []
        self.allow_order_mismatch = allow_order_mismatch

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        if not run.response_text:
             return self.make_score(sample, value=0.0, detail={"error": "no_response_text"})

        is_match, reason, parsed = self.match(
            predicted=run.response_text,
            expected=sample.expected,
            allow_order_mismatch=self.allow_order_mismatch,
            exclude_args=self.exclude_args
        )
        
        return self.make_score(
            sample, 
            value=1.0 if is_match else 0.0, 
            detail={
                "reason": reason,
                "parsed_prediction": parsed
            }
        )

    @staticmethod
    def match(
        predicted: str, 
        expected: Union[str, List[Dict[str, Any]]], 
        allow_order_mismatch: bool = False,
        exclude_args: Optional[List[str]] = None
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Static matching logic for reuse.
        Returns: (is_match, reason, parsed_prediction)
        """
        
        # 1. Parse Expected
        expected_obj = expected
        if isinstance(expected, str):
            try:
                expected_obj = json.loads(expected)
            except json.JSONDecodeError:
                return False, "Invalid JSON in expected value", None

        if not isinstance(expected_obj, list):
             return False, "Expected value must be a list of tool calls", None
            
        # 2. Parse Predicted
        pred_obj = None
        json_error = None
        
        try:
            pred_obj = json.loads(predicted)
        except json.JSONDecodeError:
            # Try finding list brackets
            start = predicted.find('[')
            end = predicted.rfind(']')
            if start != -1 and end != -1 and end > start:
                try:
                    pred_obj = json.loads(predicted[start:end+1])
                except json.JSONDecodeError as e:
                    json_error = str(e)
            else:
                 json_error = "No JSON array found"
        
        if pred_obj is None:
            return False, f"Failed to parse JSON from prediction: {json_error}", None

        if not isinstance(pred_obj, list):
            return False, "Predicted JSON is not a list", pred_obj

        # 3. Compare
        msg = ToolCallMatchMetric._compare_tool_calls(
            pred_obj, 
            expected_obj, 
            allow_order_mismatch, 
            exclude_args
        )
        
        if msg == "match":
            return True, "match", pred_obj
        else:
            return False, msg, pred_obj
            
    @staticmethod
    def _compare_tool_calls(
        pred: List[Dict[str, Any]], 
        expected: List[Dict[str, Any]],
        allow_order_mismatch: bool,
        exclude_args: Optional[List[str]]
    ) -> str:
        
        if len(pred) != len(expected):
            return f"Count mismatch: expected {len(expected)}, got {len(pred)}"
            
        if not allow_order_mismatch:
            for i, (p, e) in enumerate(zip(pred, expected)):
                if p.get("name") != e.get("name"):
                    return f"Item {i} name mismatch: expected {e.get('name')}, got {p.get('name')}"
                
                # Check args
                p_args = p.get("arguments", {})
                e_args = e.get("arguments", {})
                
                if not ToolCallMatchMetric._compare_args(p_args, e_args, exclude_args):
                     return f"Item {i} arguments mismatch"
                     
            return "match"
        else:
            # Loose order matching
            p_copy = list(pred)
            for e in expected:
                found = False
                for i, p in enumerate(p_copy):
                    if p.get("name") == e.get("name") and ToolCallMatchMetric._compare_args(p.get("arguments",{}), e.get("arguments",{}), exclude_args):
                        p_copy.pop(i)
                        found = True
                        break
                if not found:
                    return f"Missing expected call: {e.get('name')}"
            
            return "match"

    @staticmethod
    def _compare_args(a: Dict[str, Any], b: Dict[str, Any], exclude_args: Optional[List[str]]) -> bool:
        # Filter excluded args
        keys_a = set(a.keys())
        keys_b = set(b.keys())
        
        if exclude_args:
            keys_a -= set(exclude_args)
            keys_b -= set(exclude_args)
            
        if keys_a != keys_b:
            return False
            
        for k in keys_a:
            if a[k] != b[k]:
                return False
        return True
