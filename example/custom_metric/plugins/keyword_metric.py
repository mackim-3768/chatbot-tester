from typing import Any, Dict, List
from lm_eval_so.evaluator.metrics import Metric, MetricResult

class KeywordPresenceMetric(Metric):
    """
    A simple custom metric that checks if specific keywords are present in the response.
    """
    
    def __init__(self, keywords: List[str]):
        self.keywords = keywords

    def evaluate(self, response: str, reference: str | None = None, **kwargs) -> MetricResult:
        found = [k for k in self.keywords if k.lower() in response.lower()]
        score = len(found) / len(self.keywords) if self.keywords else 0.0
        
        return MetricResult(
            score=score,
            details={
                "found_keywords": found,
                "missing_keywords": [k for k in self.keywords if k not in found]
            }
        )

# Factory function to register the metric
def make_keyword_metric(config: Dict[str, Any]) -> Metric:
    return KeywordPresenceMetric(
        keywords=config.get("keywords", [])
    )

def register_metrics(registry) -> None:
    """
    This function is called by the PluginLoader when loading this module.
    """
    registry.register("keyword_presence", make_keyword_metric)
