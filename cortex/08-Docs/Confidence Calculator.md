# Confidence Calculator

## Overview

The Confidence Calculator is a quantitative decision-making tool that helps assess the reliability and certainty of decisions, insights, and architectural choices within the Cortex system.

## Purpose

- **Quantify Uncertainty**: Convert subjective confidence into measurable metrics
- **Support Decision Making**: Provide data-driven confidence scores for ADRs
- **Track Decision Quality**: Monitor how confidence predictions align with actual outcomes
- **Enable Pattern Recognition**: Identify factors that correlate with successful decisions

## Calculation Methodology

### Base Confidence Score

```
Confidence Score = (Evidence Weight + Experience Factor + Risk Assessment + Time Factor) / 4
```

### Factors

#### 1. Evidence Weight (0-100)
- **High (80-100)**: Multiple data sources, comprehensive analysis, proven patterns
- **Medium (40-79)**: Some data available, partial analysis, similar precedents
- **Low (0-39)**: Limited data, assumptions-based, novel territory

#### 2. Experience Factor (0-100)
- **High (80-100)**: Team has deep experience in this domain
- **Medium (40-79)**: Some team experience, external expertise consulted
- **Low (0-39)**: New domain for team, learning while implementing

#### 3. Risk Assessment (0-100, inverted)
- **Low Risk (80-100)**: Well-understood technology, reversible decision
- **Medium Risk (40-79)**: Some unknowns, moderate impact if wrong
- **High Risk (0-39)**: High uncertainty, significant impact if wrong

#### 4. Time Factor (0-100)
- **Adequate Time (80-100)**: Sufficient time for analysis and review
- **Limited Time (40-79)**: Some time pressure, basic analysis completed
- **Rush Decision (0-39)**: Urgent decision, minimal analysis time

## Usage in ADRs

### Standard Template Integration

```markdown
## Confidence Assessment

**Overall Confidence**: 78%

### Breakdown
- **Evidence Weight**: 85% (Strong market research, competitor analysis)
- **Experience Factor**: 75% (Team has some experience with similar APIs)
- **Risk Assessment**: 70% (Reversible decision, moderate impact)
- **Time Factor**: 80% (Adequate time for analysis)

**Risk Mitigation**: Plan for iterative improvement based on user feedback
**Review Schedule**: 3 months post-implementation
```

## Confidence Ranges

| Range | Interpretation | Action |
|-------|----------------|---------|
| 90-100% | Very High Confidence | Proceed with implementation |
| 80-89% | High Confidence | Proceed with monitoring plan |
| 70-79% | Medium Confidence | Implement with safeguards |
| 60-69% | Low Confidence | Consider alternatives or gather more data |
| 0-59% | Very Low Confidence | Do not proceed without significant risk mitigation |

## Integration Points

### With ADR System
- All architectural decisions should include confidence calculations
- Review confidence predictions against actual outcomes
- Update methodology based on learnings

### With Project Workspace
- Project risk assessment uses confidence metrics
- Resource allocation considers confidence levels
- Timeline estimates factor in uncertainty

### With Quality Gates
- Confidence thresholds for different decision types
- Automated warnings for low-confidence critical decisions
- Peer review requirements based on confidence levels

## Historical Analysis

### Decision Outcome Tracking
- Compare predicted confidence with actual results
- Identify patterns in successful vs. failed predictions
- Continuously refine calculation methodology

### Team Calibration
- Track individual and team confidence accuracy
- Provide training on better uncertainty assessment
- Develop expertise-based confidence adjustments

## Tools and Implementation

### Confidence Calculator Spreadsheet
Located at: `00-System/Tools/Confidence-Calculator.xlsx`

### API Integration
- REST endpoint for confidence calculations
- Integration with ADR template generation
- Dashboard visualization of project confidence trends

## Related Links

- [[ADR-Enhanced]] - Template includes confidence assessment
- [[Decision-Tracking]] - Process for monitoring confidence accuracy
- [[Quality-Gates]] - Confidence-based approval thresholds
- [[System-Workflows]] - Integration with decision processes
- [[Risk Management]] - Connection to risk assessment frameworks

## Version History

- **v1.0** (2025-08-10): Initial confidence calculation methodology
- **v1.1** (TBD): Refinements based on first 3 months of usage data

---

*Generated as part of Cortex system link resolution initiative*