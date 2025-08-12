#!/usr/bin/env python3
"""
Cortex Confidence Calculator v2.0
Quantitative confidence scoring for decision-making
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json


@dataclass
class SourceQuality:
    """Represents the quality metrics of a data source"""
    authority: float  # 0-1: How authoritative is the source?
    currency: float   # 0-1: How current is the information?
    relevance: float  # 0-1: How relevant to the specific decision?
    bias_level: float # 0-1: How biased is the source? (0 = no bias)


@dataclass
class DecisionData:
    """Data structure for decision analysis"""
    sources: List[SourceQuality]
    has_benchmarks: bool
    has_quantitative_data: bool
    expert_consensus_level: float  # 0-1: Level of expert agreement
    implementation_complexity: float  # 0-1: How complex to implement?
    time_sensitivity: float  # 0-1: How time-sensitive is this decision?
    contradictory_evidence: float  # 0-1: Level of contradicting information


class ConfidenceCalculator:
    """Cortex v2.0 Confidence Calculation Engine"""
    
    # Weightings based on Cortex-Development research
    WEIGHTS = {
        'data_coverage': 0.30,      # 30% - Most important factor
        'source_quality': 0.25,     # 25% - Authority and currency
        'expert_consensus': 0.20,   # 20% - Agreement level
        'time_sensitivity': 0.15,   # 15% - Currency factor
        'implementation_risk': 0.10 # 10% - Complexity risk
    }
    
    def calculate_confidence(self, decision_data: DecisionData) -> Dict:
        """Calculate comprehensive confidence score"""
        
        # 1. Data Coverage Score (30%)
        data_coverage = self._calculate_data_coverage(decision_data)
        
        # 2. Source Quality Score (25%)
        source_quality = self._calculate_source_quality(decision_data)
        
        # 3. Expert Consensus Score (20%)
        expert_consensus = decision_data.expert_consensus_level * 100
        
        # 4. Time Sensitivity Score (15%)
        time_sensitivity = self._calculate_time_sensitivity(decision_data)
        
        # 5. Implementation Risk Score (10%)
        implementation_risk = self._calculate_implementation_risk(decision_data)
        
        # Weighted final confidence
        confidence = (
            data_coverage * self.WEIGHTS['data_coverage'] +
            source_quality * self.WEIGHTS['source_quality'] +
            expert_consensus * self.WEIGHTS['expert_consensus'] +
            time_sensitivity * self.WEIGHTS['time_sensitivity'] +
            implementation_risk * self.WEIGHTS['implementation_risk']
        )
        
        # Apply contradiction penalty
        contradiction_penalty = decision_data.contradictory_evidence * 15
        confidence = max(0, confidence - contradiction_penalty)
        
        return {
            'overall_confidence': min(confidence, 100),
            'breakdown': {
                'data_coverage': data_coverage,
                'source_quality': source_quality,
                'expert_consensus': expert_consensus,
                'time_sensitivity': time_sensitivity,
                'implementation_risk': implementation_risk,
                'contradiction_penalty': contradiction_penalty
            },
            'recommendation': self._get_recommendation(confidence)
        }
    
    def _calculate_data_coverage(self, data: DecisionData) -> float:
        """Calculate data completeness score"""
        score = 0
        
        # Base score from number of sources
        source_count = len(data.sources)
        if source_count >= 4:
            score += 40
        elif source_count >= 2:
            score += 25
        elif source_count >= 1:
            score += 10
        
        # Bonus for quantitative data
        if data.has_quantitative_data:
            score += 30
        
        # Bonus for benchmarks
        if data.has_benchmarks:
            score += 30
        
        return min(score, 100)
    
    def _calculate_source_quality(self, data: DecisionData) -> float:
        """Calculate weighted source quality score"""
        if not data.sources:
            return 0
        
        total_quality = 0
        for source in data.sources:
            # Authority is most important for source quality
            authority_score = source.authority * 40
            currency_score = source.currency * 30
            relevance_score = source.relevance * 20
            bias_penalty = source.bias_level * 10
            
            source_score = authority_score + currency_score + relevance_score - bias_penalty
            total_quality += max(0, source_score)
        
        return min(total_quality / len(data.sources), 100)
    
    def _calculate_time_sensitivity(self, data: DecisionData) -> float:
        """Calculate time sensitivity impact on confidence"""
        # Higher time sensitivity = lower confidence (need to act fast)
        base_score = (1 - data.time_sensitivity) * 80 + 20
        return base_score
    
    def _calculate_implementation_risk(self, data: DecisionData) -> float:
        """Calculate implementation risk score"""
        # Lower complexity = higher confidence
        risk_score = (1 - data.implementation_complexity) * 100
        return risk_score
    
    def _get_recommendation(self, confidence: float) -> str:
        """Get action recommendation based on confidence level"""
        if confidence >= 90:
            return "🟢 PROCEED - High confidence decision"
        elif confidence >= 70:
            return "🟡 PROCEED WITH MONITORING - Medium confidence"
        elif confidence >= 50:
            return "🟠 MORE RESEARCH NEEDED - Low confidence"
        else:
            return "🔴 DO NOT PROCEED - Insufficient confidence"


# Example usage and testing
def example_usage():
    """Example of how to use the confidence calculator"""
    
    # Example: Strong decision with good data
    strong_sources = [
        SourceQuality(authority=0.9, currency=0.8, relevance=0.9, bias_level=0.1),
        SourceQuality(authority=0.8, currency=0.9, relevance=0.8, bias_level=0.2),
        SourceQuality(authority=0.7, currency=0.7, relevance=0.9, bias_level=0.1),
    ]
    
    strong_decision = DecisionData(
        sources=strong_sources,
        has_benchmarks=True,
        has_quantitative_data=True,
        expert_consensus_level=0.9,
        implementation_complexity=0.3,
        time_sensitivity=0.2,
        contradictory_evidence=0.1
    )
    
    calculator = ConfidenceCalculator()
    result = calculator.calculate_confidence(strong_decision)
    
    print("=== Cortex Confidence Analysis ===")
    print(f"Overall Confidence: {result['overall_confidence']:.1f}%")
    print(f"Recommendation: {result['recommendation']}")
    print("\nBreakdown:")
    for factor, score in result['breakdown'].items():
        print(f"  {factor}: {score:.1f}")


if __name__ == "__main__":
    example_usage()
