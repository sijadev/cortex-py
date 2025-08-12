#!/usr/bin/env python3
"""
Cortex Confidence Calculator v2.1
Enhanced for CLI integration with Rich UI support
Migrated from 00-System/Algorithms/confidence_calculator.py
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from pathlib import Path

console = Console()

@dataclass
class SourceQuality:
    """Represents the quality metrics of a data source"""
    authority: float  # 0-1: How authoritative is the source?
    currency: float   # 0-1: How current is the information?
    relevance: float  # 0-1: How relevant to the specific decision?
    bias_level: float # 0-1: How biased is the source? (0 = no bias)
    name: Optional[str] = None  # Source name for CLI display

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
    decision_name: Optional[str] = None  # Decision name for CLI display

class ConfidenceCalculator:
    """Cortex v2.1 Confidence Calculation Engine with CLI enhancements"""
    
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
            'recommendation': self._get_recommendation(confidence),
            'risk_level': self._get_risk_level(confidence),
            'next_steps': self._get_next_steps(confidence, decision_data)
        }
    
    def display_confidence_analysis(self, result: Dict, decision_name: str = "Decision"):
        """Display confidence analysis with Rich formatting"""
        confidence = result['overall_confidence']
        recommendation = result['recommendation']
        
        # Main confidence panel
        confidence_color = self._get_confidence_color(confidence)
        panel_content = f"[bold {confidence_color}]{confidence:.1f}%[/bold {confidence_color}]\n\n{recommendation}"
        
        console.print(Panel(
            panel_content,
            title=f"📊 Confidence Analysis: {decision_name}",
            style=confidence_color
        ))
        
        # Breakdown table
        table = Table(title="🔍 Detailed Breakdown")
        table.add_column("Factor", style="cyan", width=20)
        table.add_column("Score", style="white", width=10)
        table.add_column("Weight", style="yellow", width=10) 
        table.add_column("Contribution", style="green", width=15)
        
        breakdown = result['breakdown']
        for factor, score in breakdown.items():
            if factor == 'contradiction_penalty':
                table.add_row(
                    "Contradiction Penalty",
                    f"{score:.1f}",
                    "-",
                    f"[red]-{score:.1f}[/red]"
                )
            elif factor in self.WEIGHTS:
                weight = self.WEIGHTS[factor] * 100
                contribution = score * self.WEIGHTS[factor]
                table.add_row(
                    factor.replace('_', ' ').title(),
                    f"{score:.1f}",
                    f"{weight:.0f}%",
                    f"{contribution:.1f}"
                )
        
        console.print(table)
        
        # Next steps
        if result.get('next_steps'):
            console.print("\n💡 [bold blue]Recommended Next Steps:[/bold blue]")
            for step in result['next_steps']:
                console.print(f"  • {step}")
    
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
    
    def _get_risk_level(self, confidence: float) -> str:
        """Get risk level classification"""
        if confidence >= 90:
            return "LOW"
        elif confidence >= 70:
            return "MEDIUM"
        elif confidence >= 50:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence display"""
        if confidence >= 90:
            return "green"
        elif confidence >= 70:
            return "yellow"
        elif confidence >= 50:
            return "orange3"
        else:
            return "red"
    
    def _get_next_steps(self, confidence: float, data: DecisionData) -> List[str]:
        """Get recommended next steps based on confidence analysis"""
        steps = []
        
        if confidence < 50:
            steps.append("Gather more high-authority sources")
            if not data.has_quantitative_data:
                steps.append("Seek quantitative data to support the decision")
            if len(data.sources) < 3:
                steps.append("Consult additional experts or references")
        
        elif confidence < 70:
            steps.append("Consider pilot implementation or testing")
            if data.contradictory_evidence > 0.3:
                steps.append("Resolve contradictory evidence before proceeding")
            steps.append("Set up monitoring mechanisms")
        
        elif confidence < 90:
            steps.append("Proceed with careful monitoring")
            steps.append("Document decision rationale")
        
        else:
            steps.append("Proceed with confidence")
            steps.append("Document successful decision process for future reference")
        
        if data.time_sensitivity > 0.7:
            steps.insert(0, "⚡ Time-sensitive: Make decision quickly")
        
        return steps

def load_decision_data(file_path: Union[str, Path]) -> DecisionData:
    """Load decision data from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Convert source dictionaries to SourceQuality objects
    sources = [SourceQuality(**source) for source in data['sources']]
    
    return DecisionData(
        sources=sources,
        has_benchmarks=data['has_benchmarks'],
        has_quantitative_data=data['has_quantitative_data'],
        expert_consensus_level=data['expert_consensus_level'],
        implementation_complexity=data['implementation_complexity'],
        time_sensitivity=data['time_sensitivity'],
        contradictory_evidence=data['contradictory_evidence'],
        decision_name=data.get('decision_name', 'Unnamed Decision')
    )

def create_example_data() -> DecisionData:
    """Create example decision data for testing"""
    sources = [
        SourceQuality(authority=0.9, currency=0.8, relevance=0.9, bias_level=0.1, name="Expert Study"),
        SourceQuality(authority=0.8, currency=0.9, relevance=0.8, bias_level=0.2, name="Industry Report"),
        SourceQuality(authority=0.7, currency=0.7, relevance=0.9, bias_level=0.1, name="Case Study"),
    ]
    
    return DecisionData(
        sources=sources,
        has_benchmarks=True,
        has_quantitative_data=True,
        expert_consensus_level=0.9,
        implementation_complexity=0.3,
        time_sensitivity=0.2,
        contradictory_evidence=0.1,
        decision_name="API Architecture Decision"
    )

# CLI Commands (to be integrated into main CLI)
@click.group()
def confidence():
    """Confidence calculation and decision analysis tools"""
    pass

@confidence.command()
@click.option('--input', '-i', type=click.Path(exists=True), help='JSON file with decision data')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--format', 'output_format', type=click.Choice(['json', 'display']), default='display')
def calculate(input, output, output_format):
    """Calculate confidence score for a decision"""
    try:
        if input:
            decision_data = load_decision_data(input)
        else:
            # Use example data
            console.print("ℹ️  No input file provided, using example data", style="blue")
            decision_data = create_example_data()
        
        calculator = ConfidenceCalculator()
        result = calculator.calculate_confidence(decision_data)
        
        if output_format == 'json':
            if output:
                with open(output, 'w') as f:
                    json.dump(result, f, indent=2)
                console.print(f"✅ Results saved to {output}")
            else:
                print(json.dumps(result, indent=2))
        else:
            calculator.display_confidence_analysis(result, decision_data.decision_name or "Decision")
        
    except Exception as e:
        console.print(f"❌ [red]Error calculating confidence: {e}[/red]")

@confidence.command()
def example():
    """Show example decision analysis"""
    decision_data = create_example_data()
    calculator = ConfidenceCalculator()
    result = calculator.calculate_confidence(decision_data)
    calculator.display_confidence_analysis(result, decision_data.decision_name)

if __name__ == "__main__":
    confidence()
