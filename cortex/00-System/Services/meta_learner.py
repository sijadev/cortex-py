#!/usr/bin/env python3
"""
Cortex Meta-Learning Engine
Self-improvement and optimization algorithms
"""

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class LearningMetric:
    """Metric for measuring learning effectiveness"""
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_rate: float
    last_updated: str

class CortexMetaLearner:
    """Self-improvement engine for Cortex system"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = cortex_path
        self.meta_data_path = cortex_path / "00-System" / "Services" / "data" / "meta_learning.json"
        self.improvement_log = cortex_path / "00-System" / "Services" / "logs" / "self_improvement.log"
        
        self.learning_metrics = self.load_learning_metrics()
        
    def analyze_confidence_accuracy(self) -> Dict:
        """
        Analyze how well confidence predictions match actual outcomes
        Suggest algorithm improvements
        """
        decisions = self._load_decision_outcomes()
        
        if len(decisions) < 5:  # Need minimum data
            return {"status": "insufficient_data", "recommendations": []}
        
        # Calculate confidence vs outcome correlation
        confidence_scores = [d["predicted_confidence"] for d in decisions if "predicted_confidence" in d]
        actual_outcomes = [d["actual_success"] for d in decisions if "actual_success" in d]
        
        if len(confidence_scores) != len(actual_outcomes):
            return {"status": "data_mismatch", "recommendations": []}
        
        # Simple correlation analysis
        correlation = self._calculate_correlation(confidence_scores, actual_outcomes)
        
        recommendations = []
        
        # Algorithm improvement suggestions
        if correlation < 0.7:  # Poor correlation
            recommendations.append({
                "type": "algorithm_adjustment",
                "priority": "high",
                "description": "Confidence algorithm poorly predicts outcomes",
                "suggestion": "Reduce weight of factors with poor predictive power",
                "data": {
                    "current_correlation": correlation,
                    "target_correlation": 0.8,
                    "improvement_needed": 0.8 - correlation
                }
            })
        
        # Factor analysis
        factor_performance = self._analyze_factor_effectiveness(decisions)
        for factor, performance in factor_performance.items():
            if performance["predictive_power"] < 0.5:
                recommendations.append({
                    "type": "factor_adjustment", 
                    "priority": "medium",
                    "description": f"Factor '{factor}' has low predictive power",
                    "suggestion": f"Reduce weight of '{factor}' in confidence calculation",
                    "data": performance
                })
        
        return {
            "status": "analysis_complete",
            "correlation": correlation,
            "factor_performance": factor_performance,
            "recommendations": recommendations
        }
    
    def optimize_pattern_detection(self) -> Dict:
        """
        Analyze pattern detection effectiveness
        Improve pattern recognition algorithms
        """
        patterns = self._load_pattern_applications()
        
        optimizations = []
        
        for pattern in patterns:
            success_rate = pattern.get("success_rate", 0)
            application_count = pattern.get("application_count", 0)
            
            if application_count >= 3:  # Enough data for analysis
                if success_rate < 0.6:  # Poor performance
                    optimizations.append({
                        "pattern_name": pattern["name"],
                        "action": "deprecate",
                        "reason": f"Low success rate: {success_rate:.2f}",
                        "recommendation": "Remove or significantly refine pattern"
                    })
                elif success_rate > 0.9:  # Excellent performance
                    optimizations.append({
                        "pattern_name": pattern["name"],
                        "action": "promote",
                        "reason": f"High success rate: {success_rate:.2f}",
                        "recommendation": "Increase pattern detection sensitivity"
                    })
        
        return {
            "optimizations": optimizations,
            "pattern_count": len(patterns),
            "avg_success_rate": sum(p.get("success_rate", 0) for p in patterns) / len(patterns) if patterns else 0
        }
    
    def improve_templates(self) -> Dict:
        """
        Analyze template usage and effectiveness
        Suggest template improvements
        """
        template_usage = self._analyze_template_usage()
        
        improvements = []
        
        for template_name, usage_data in template_usage.items():
            completion_rate = usage_data.get("completion_rate", 0)
            effectiveness_score = usage_data.get("effectiveness_score", 0)
            unused_sections = usage_data.get("unused_sections", [])
            
            if completion_rate < 0.7:  # Low completion rate
                improvements.append({
                    "template": template_name,
                    "issue": "low_completion_rate",
                    "current_rate": completion_rate,
                    "suggestion": "Simplify template or remove optional sections",
                    "unused_sections": unused_sections
                })
            
            if effectiveness_score < 0.6:  # Low effectiveness
                improvements.append({
                    "template": template_name,
                    "issue": "low_effectiveness",
                    "current_score": effectiveness_score,
                    "suggestion": "Restructure template based on successful usage patterns"
                })
        
        return {
            "improvements": improvements,
            "template_count": len(template_usage),
            "avg_completion_rate": sum(data.get("completion_rate", 0) for data in template_usage.values()) / len(template_usage) if template_usage else 0
        }
    
    def adaptive_threshold_optimization(self) -> Dict:
        """
        Optimize thresholds based on system performance
        """
        current_thresholds = self._get_current_thresholds()
        performance_data = self._get_performance_data()
        
        optimized_thresholds = {}
        
        for threshold_name, current_value in current_thresholds.items():
            performance_at_threshold = performance_data.get(threshold_name, {})
            
            if "false_positive_rate" in performance_at_threshold:
                fp_rate = performance_at_threshold["false_positive_rate"]
                fn_rate = performance_at_threshold["false_negative_rate"]
                
                # Optimize threshold to minimize total error
                if fp_rate > 0.2:  # Too many false positives
                    optimized_thresholds[threshold_name] = current_value + 0.1
                elif fn_rate > 0.2:  # Too many false negatives
                    optimized_thresholds[threshold_name] = current_value - 0.1
                else:
                    optimized_thresholds[threshold_name] = current_value
        
        return {
            "current_thresholds": current_thresholds,
            "optimized_thresholds": optimized_thresholds,
            "performance_improvement_expected": self._estimate_improvement(current_thresholds, optimized_thresholds)
        }
    
    def generate_system_improvements(self) -> Dict:
        """
        Generate comprehensive system improvement recommendations
        """
        confidence_analysis = self.analyze_confidence_accuracy()
        pattern_optimization = self.optimize_pattern_detection()
        template_improvements = self.improve_templates()
        threshold_optimization = self.adaptive_threshold_optimization()
        
        # Prioritize improvements by impact
        all_improvements = []
        
        # High impact: Confidence algorithm improvements
        for rec in confidence_analysis.get("recommendations", []):
            if rec["priority"] == "high":
                all_improvements.append({
                    "category": "confidence_algorithm",
                    "impact": "high",
                    "effort": "medium",
                    **rec
                })
        
        # Medium impact: Pattern optimizations
        for opt in pattern_optimization.get("optimizations", []):
            all_improvements.append({
                "category": "pattern_detection",
                "impact": "medium", 
                "effort": "low",
                **opt
            })
        
        # Lower impact: Template improvements
        for imp in template_improvements.get("improvements", []):
            all_improvements.append({
                "category": "templates",
                "impact": "low",
                "effort": "low",
                **imp
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_improvements": len(all_improvements),
            "high_impact_count": len([i for i in all_improvements if i["impact"] == "high"]),
            "improvements": sorted(all_improvements, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["impact"]], reverse=True),
            "system_health_score": self._calculate_system_health(),
            "learning_velocity": self._calculate_learning_velocity()
        }
    
    def apply_improvements(self, improvements: List[Dict]) -> Dict:
        """
        Automatically apply safe improvements
        """
        applied_improvements = []
        skipped_improvements = []
        
        for improvement in improvements:
            if improvement.get("effort") == "low" and improvement.get("category") in ["pattern_detection", "templates"]:
                # Safe to auto-apply
                try:
                    if improvement["category"] == "pattern_detection" and improvement.get("action") == "deprecate":
                        self._deprecate_pattern(improvement["pattern_name"])
                        applied_improvements.append(improvement)
                    
                    elif improvement["category"] == "templates":
                        self._log_template_improvement(improvement)
                        applied_improvements.append(improvement)
                        
                except Exception as e:
                    skipped_improvements.append({**improvement, "error": str(e)})
            else:
                # Requires human review
                skipped_improvements.append({**improvement, "reason": "requires_human_review"})
        
        return {
            "applied": applied_improvements,
            "skipped": skipped_improvements,
            "auto_applied_count": len(applied_improvements),
            "human_review_required": len(skipped_improvements)
        }
    
    def _load_decision_outcomes(self) -> List[Dict]:
        """Load decision data with outcomes for analysis"""
        # Implementation would load from monitoring data
        return []
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _analyze_factor_effectiveness(self, decisions: List[Dict]) -> Dict:
        """Analyze which factors predict success best"""
        # Implementation would analyze correlation between factors and outcomes
        return {}
    
    def _load_pattern_applications(self) -> List[Dict]:
        """Load pattern application data"""
        # Implementation would load from pattern usage tracking
        return []
    
    def _analyze_template_usage(self) -> Dict:
        """Analyze template usage patterns"""
        # Implementation would analyze template completion and effectiveness
        return {}
    
    def _get_current_thresholds(self) -> Dict:
        """Get current system thresholds"""
        return {
            "pattern_detection_threshold": 0.7,
            "confidence_threshold": 0.7,
            "quality_alert_threshold": 0.8
        }
    
    def _get_performance_data(self) -> Dict:
        """Get performance data for threshold optimization"""
        return {}
    
    def _estimate_improvement(self, current: Dict, optimized: Dict) -> float:
        """Estimate performance improvement from threshold changes"""
        return 0.05  # Placeholder
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health score"""
        return 0.85  # Placeholder
    
    def _calculate_learning_velocity(self) -> float:
        """Calculate how fast the system is improving"""
        return 0.1  # Placeholder - 10% improvement per month
    
    def _deprecate_pattern(self, pattern_name: str):
        """Mark a pattern as deprecated"""
        pass
    
    def _log_template_improvement(self, improvement: Dict):
        """Log template improvement suggestion"""
        pass
    
    def load_learning_metrics(self) -> Dict:
        """Load learning performance metrics"""
        if self.meta_data_path.exists():
            with open(self.meta_data_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_learning_metrics(self, metrics: Dict):
        """Save learning performance metrics"""
        with open(self.meta_data_path, 'w') as f:
            json.dump(metrics, f, indent=2)

# Example usage
if __name__ == "__main__":
    learner = CortexMetaLearner(Path("/Users/simonjanke/Projects/cortex"))
    improvements = learner.generate_system_improvements()
    
    print("=== Cortex Self-Improvement Analysis ===")
    print(f"System Health Score: {improvements['system_health_score']:.2f}")
    print(f"Learning Velocity: {improvements['learning_velocity']:.2f}")
    print(f"Total Improvements Available: {improvements['total_improvements']}")
    print(f"High Impact Improvements: {improvements['high_impact_count']}")
    
    # Apply safe improvements automatically
    applied = learner.apply_improvements(improvements['improvements'])
    print(f"\nAuto-Applied: {applied['auto_applied_count']}")
    print(f"Human Review Required: {applied['human_review_required']}")
