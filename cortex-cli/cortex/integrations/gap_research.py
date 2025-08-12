#!/usr/bin/env python3
"""
Cortex Gap-Aware Web Research Integration
Real-time gap detection with intelligent web research
"""

import json
import asyncio
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class ResearchResult:
    """Structured research result"""
    query: str
    title: str
    url: str
    content: str
    relevance_score: float
    authority_score: float
    currency_score: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'query': self.query,
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'relevance_score': self.relevance_score,
            'authority_score': self.authority_score,
            'currency_score': self.currency_score,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class KnowledgeGap:
    """Structured knowledge gap information"""
    gap_id: str
    title: str
    gap_type: str
    priority: str
    confidence: float
    description: str
    context: str
    detected_date: str
    research_queries: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGap':
        """Create from dictionary data"""
        return cls(
            gap_id=data.get('gap_id', ''),
            title=data.get('title', ''),
            gap_type=data.get('gap_type', 'unknown'),
            priority=data.get('priority', 'medium'),
            confidence=data.get('confidence', 0.5),
            description=data.get('description', ''),
            context=data.get('context', ''),
            detected_date=data.get('detected_date', ''),
            research_queries=data.get('research_queries', [])
        )

@dataclass
class GapFillReport:
    """Complete gap fill report"""
    gap_id: str
    gap_info: KnowledgeGap
    research_results: List[ResearchResult]
    content: str
    file_path: str
    completion_timestamp: datetime
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            'gap_id': self.gap_id,
            'sources_count': len(self.research_results),
            'avg_relevance': sum(r.relevance_score for r in self.research_results) / len(self.research_results) if self.research_results else 0,
            'avg_authority': sum(r.authority_score for r in self.research_results) / len(self.research_results) if self.research_results else 0,
            'word_count': len(self.content.split()),
            'completed_at': self.completion_timestamp.isoformat()
        }

class GapResearchIntegrator:
    """
    Cortex Gap-Aware Web Research Integration Engine
    
    Integrates gap detection with intelligent web research capabilities,
    providing automated knowledge gap filling through structured research.
    """
    
    def __init__(self, cortex_path: Optional[str] = None):
        """Initialize the gap research integrator"""
        self.cortex_path = Path(cortex_path or "/Users/simonjanke/Projects/cortex")
        self.data_path = self.cortex_path / "00-System" / "AI-Learning-Engine" / "data"
        self.research_requests_file = self.data_path / "research_requests.json"
        self.gap_fills_path = self.cortex_path / "05-Insights" / "Auto-Gap-Fills"
        self.gaps_file = self.data_path / "knowledge_gaps" / "detected_gaps.json"
        
        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.gap_fills_path.mkdir(parents=True, exist_ok=True)
        (self.data_path / "knowledge_gaps").mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        if not self.logger.handlers:
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def check_pending_research_requests(self) -> List[Dict[str, Any]]:
        """Check for pending research requests from gap detection"""
        
        if not self.research_requests_file.exists():
            return []
        
        try:
            with open(self.research_requests_file, 'r', encoding='utf-8') as f:
                requests = json.load(f)
            
            # Filter for pending requests
            pending = [req for req in requests if req.get('status') == 'pending_claude_research']
            
            return pending
        
        except Exception as e:
            self.logger.error(f"Error reading research requests: {e}")
            return []
    
    def get_knowledge_gaps(self) -> List[KnowledgeGap]:
        """Get all detected knowledge gaps"""
        
        if not self.gaps_file.exists():
            return []
        
        try:
            with open(self.gaps_file, 'r', encoding='utf-8') as f:
                gaps_data = json.load(f)
            
            return [KnowledgeGap.from_dict(gap) for gap in gaps_data]
        
        except Exception as e:
            self.logger.error(f"Error reading gaps data: {e}")
            return []
    
    def get_knowledge_gap(self, gap_id: str) -> Optional[KnowledgeGap]:
        """Get specific knowledge gap by ID"""
        
        gaps = self.get_knowledge_gaps()
        for gap in gaps:
            if gap.gap_id == gap_id:
                return gap
        
        return None
    
    def get_research_queries_for_gap(self, gap_id: str) -> List[str]:
        """Get specific research queries for a gap"""
        
        gap = self.get_knowledge_gap(gap_id)
        return gap.research_queries if gap else []
    
    def create_research_template(self, gap_id: str) -> Optional[Dict[str, Any]]:
        """Create research template for AI agent to fill"""
        
        queries = self.get_research_queries_for_gap(gap_id)
        
        if not queries:
            self.logger.warning(f"No research queries found for gap {gap_id}")
            return None
        
        # Create structured template for research
        template = {
            'gap_id': gap_id,
            'queries_researched': queries[:5],  # Limit to top 5 queries
            'research_method': 'ai_web_search',
            'timestamp': datetime.now().isoformat(),
            'status': 'template_created',
            'results': []
        }
        
        # Add placeholder for each query
        for query in queries[:5]:
            template['results'].append({
                'query': query,
                'title': 'TO_BE_FILLED',
                'url': 'TO_BE_FILLED',
                'content': 'TO_BE_FILLED',
                'relevance_score': 0.0,
                'authority_score': 0.0,
                'currency_score': 0.0,
                'notes': 'Research findings to be added here'
            })
        
        return template
    
    def validate_research_results(self, results: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate research results for completeness and quality"""
        
        errors = []
        
        if not results:
            errors.append("No research results provided")
            return False, errors
        
        for i, result in enumerate(results):
            result_num = i + 1
            
            # Check required fields
            required_fields = ['query', 'title', 'url', 'content']
            for field in required_fields:
                if not result.get(field) or result[field] == 'TO_BE_FILLED':
                    errors.append(f"Result {result_num}: Missing or incomplete {field}")
            
            # Check content quality
            content = result.get('content', '')
            if content and len(content.strip()) < 50:
                errors.append(f"Result {result_num}: Content too short (minimum 50 characters)")
            
            # Check scores
            score_fields = ['relevance_score', 'authority_score', 'currency_score']
            for score_field in score_fields:
                score = result.get(score_field, 0)
                if not isinstance(score, (int, float)) or score < 0 or score > 1:
                    errors.append(f"Result {result_num}: {score_field} must be between 0 and 1")
            
            # Check URL format
            url = result.get('url', '')
            if url and url != 'TO_BE_FILLED':
                if not url.startswith(('http://', 'https://')):
                    errors.append(f"Result {result_num}: Invalid URL format")
        
        return len(errors) == 0, errors
    
    def generate_gap_fill_content(self, gap: KnowledgeGap, research_results: List[ResearchResult]) -> str:
        """Generate structured content to fill a knowledge gap"""
        
        content = f"""# {gap.title} - Auto Research Fill

*Knowledge gap automatically filled by Cortex Gap Detection & Web Research*

## Gap Information
- **Gap ID**: {gap.gap_id}
- **Type**: {gap.gap_type}
- **Priority**: {gap.priority}
- **Confidence**: {gap.confidence:.1%}
- **Detected**: {gap.detected_date}
- **Research Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Gap Description
{gap.description}

## Research Context
**Original Context**: {gap.context}

## Research Results

Based on targeted web research with {len(research_results)} sources:

"""
        
        # Add research results
        for i, result in enumerate(research_results, 1):
            content += f"""### Source {i}: {result.title}

**URL**: {result.url}  
**Query**: {result.query}  
**Relevance**: {result.relevance_score:.1%}  
**Authority**: {result.authority_score:.1%}  
**Currency**: {result.currency_score:.1%}

**Key Findings**:
{result.content[:800]}{'...' if len(result.content) > 800 else ''}

"""
        
        # Add synthesis section based on gap type
        content += f"""## Synthesis & Integration

### Key Insights Discovered:
"""
        
        # Type-specific insights
        if gap.gap_type == 'missing_benchmarks':
            content += """
- Performance benchmarks and metrics identified
- Industry standard comparisons available
- Measurement criteria established
"""
        elif gap.gap_type == 'incomplete_research':
            content += """
- Additional research sources integrated
- Missing perspectives covered
- Knowledge base expanded
"""
        elif gap.gap_type == 'missing_examples':
            content += """
- Practical examples and use cases added
- Implementation patterns identified
- Real-world applications documented
"""
        elif gap.gap_type == 'missing_alternatives':
            content += """
- Alternative solutions researched
- Comparative analysis completed
- Decision criteria clarified
"""
        else:
            content += f"""
- Gap type '{gap.gap_type}' analysis completed
- Knowledge foundation strengthened
- Information gaps addressed
"""
        
        # Calculate research quality metrics
        avg_relevance = sum(r.relevance_score for r in research_results) / len(research_results) if research_results else 0
        avg_authority = sum(r.authority_score for r in research_results) / len(research_results) if research_results else 0
        
        content += f"""
### Research Quality Assessment:
- **Average Relevance**: {avg_relevance:.1%}
- **Average Authority**: {avg_authority:.1%}
- **Sources Count**: {len(research_results)}
- **Research Depth**: {'High' if len(research_results) >= 3 else 'Medium' if len(research_results) >= 2 else 'Basic'}

### Recommended Actions:
1. **Integrate findings** into original decision/research document
2. **Update confidence scores** based on additional information
3. **Review implications** for related decisions
4. **Apply learnings** to similar future decisions
5. **Archive this gap fill** for future reference

### Research Queries Used:
"""
        
        for query in gap.research_queries:
            content += f"- {query}\n"
        
        content += f"""
---

## Cortex Integration Notes

**Gap Status**: ✅ Filled via targeted web research  
**Quality Check**: Research results meet minimum quality thresholds  
**Integration**: Ready for manual review and integration  

**Next Steps**:
1. Review research quality and relevance
2. Integrate key findings into original context
3. Update decision confidence if applicable
4. Archive this gap fill document

**Auto-Generated Tags**: #{gap.gap_type} #research-fill #knowledge-gap #cortex-ai

---
*Auto-generated by Cortex Gap Detection Engine v2.0*  
*Research completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def save_gap_fill(self, gap_id: str, content: str) -> str:
        """Save gap fill content to file"""
        
        filename = f"Gap-Fill-{gap_id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.gap_fills_path / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Gap fill saved: {file_path}")
            return str(file_path)
        
        except Exception as e:
            self.logger.error(f"Error saving gap fill: {e}")
            raise
    
    def mark_research_completed(self, gap_id: str, research_summary: Dict[str, Any]) -> bool:
        """Mark a research request as completed and save results"""
        
        try:
            # Update research requests
            requests = []
            if self.research_requests_file.exists():
                with open(self.research_requests_file, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
            
            # Update status
            for req in requests:
                if req.get('gap_id') == gap_id:
                    req['status'] = 'completed'
                    req['completed_at'] = datetime.now().isoformat()
                    req['results_summary'] = research_summary
            
            # Save updated requests
            with open(self.research_requests_file, 'w', encoding='utf-8') as f:
                json.dump(requests, f, indent=2, ensure_ascii=False)
            
            # Save detailed results
            results_file = self.gap_fills_path / f"research_results_{gap_id}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(research_summary, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error marking research completed: {e}")
            return False
    
    def create_gap_fill_report(self, gap_id: str, research_data: List[Dict[str, Any]]) -> Optional[GapFillReport]:
        """Create complete gap fill report"""
        
        # Get gap information
        gap = self.get_knowledge_gap(gap_id)
        if not gap:
            self.logger.error(f"Gap {gap_id} not found")
            return None
        
        # Validate research data
        is_valid, errors = self.validate_research_results(research_data)
        if not is_valid:
            self.logger.error(f"Invalid research data: {errors}")
            return None
        
        # Convert to ResearchResult objects
        research_results = []
        for result_data in research_data:
            research_results.append(ResearchResult(
                query=result_data.get('query', ''),
                title=result_data.get('title', ''),
                url=result_data.get('url', ''),
                content=result_data.get('content', ''),
                relevance_score=result_data.get('relevance_score', 0.0),
                authority_score=result_data.get('authority_score', 0.0),
                currency_score=result_data.get('currency_score', 0.0),
                timestamp=datetime.now()
            ))
        
        # Generate content
        content = self.generate_gap_fill_content(gap, research_results)
        
        # Save to file
        file_path = self.save_gap_fill(gap_id, content)
        
        # Create report
        report = GapFillReport(
            gap_id=gap_id,
            gap_info=gap,
            research_results=research_results,
            content=content,
            file_path=file_path,
            completion_timestamp=datetime.now()
        )
        
        # Mark as completed
        summary = report.get_summary_stats()
        summary['gap_fill_file'] = file_path
        summary['research_quality'] = 'ai_verified'
        
        self.mark_research_completed(gap_id, summary)
        
        return report
    
    def get_gap_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about gaps and research"""
        
        gaps = self.get_knowledge_gaps()
        pending_requests = self.check_pending_research_requests()
        
        # Count by type
        gap_types = {}
        priority_counts = {}
        for gap in gaps:
            gap_types[gap.gap_type] = gap_types.get(gap.gap_type, 0) + 1
            priority_counts[gap.priority] = priority_counts.get(gap.priority, 0) + 1
        
        # Count completed gap fills
        completed_fills = len(list(self.gap_fills_path.glob("Gap-Fill-*.md")))
        
        return {
            'total_gaps': len(gaps),
            'pending_research': len(pending_requests),
            'completed_fills': completed_fills,
            'completion_rate': completed_fills / len(gaps) if gaps else 0,
            'gap_types': gap_types,
            'priority_distribution': priority_counts,
            'avg_confidence': sum(gap.confidence for gap in gaps) / len(gaps) if gaps else 0
        }
    
    def run_gap_detection(self) -> bool:
        """Run the gap detection engine"""
        
        try:
            gap_detection_script = self.cortex_path / "00-System" / "AI-Learning-Engine" / "gap_detection_engine.py"
            
            if not gap_detection_script.exists():
                self.logger.warning(f"Gap detection script not found: {gap_detection_script}")
                return False
            
            result = subprocess.run([
                sys.executable, str(gap_detection_script)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("Gap detection completed successfully")
                return True
            else:
                self.logger.error(f"Gap detection failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.logger.error("Gap detection timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running gap detection: {e}")
            return False

# Convenience functions for external usage
def perform_gap_research_with_ai(gap_id: str) -> Optional[Dict[str, Any]]:
    """Function for AI agents to perform web research for a specific gap"""
    
    integrator = GapResearchIntegrator()
    
    # Get research template
    template = integrator.create_research_template(gap_id)
    
    if not template:
        print(f"❌ No research template could be created for gap {gap_id}")
        return None
    
    print(f"🔍 Research template created for gap {gap_id}")
    print(f"📋 Queries: {template['queries_researched']}")
    print(f"📊 Ready for AI agent to fill research results")
    
    return template

def complete_gap_research(gap_id: str, research_results: List[Dict[str, Any]]) -> Optional[str]:
    """Complete gap research after AI agent has filled in the data"""
    
    integrator = GapResearchIntegrator()
    
    try:
        # Create comprehensive report
        report = integrator.create_gap_fill_report(gap_id, research_results)
        
        if report:
            print(f"✅ Gap research completed for {gap_id}")
            print(f"📄 Gap fill saved: {report.file_path}")
            print(f"📊 Sources: {len(report.research_results)}")
            
            # Show summary stats
            stats = report.get_summary_stats()
            print(f"📈 Avg relevance: {stats['avg_relevance']:.1%}")
            print(f"📈 Avg authority: {stats['avg_authority']:.1%}")
            
            return report.file_path
        else:
            print(f"❌ Error completing gap research for {gap_id}")
            return None
    
    except Exception as e:
        print(f"❌ Error in gap research completion: {e}")
        return None

def run_gap_detection_and_prepare_research() -> Dict[str, Any]:
    """Run gap detection and prepare research requests for AI agents"""
    
    print("🔍 Running Cortex Gap Detection...")
    integrator = GapResearchIntegrator()
    
    # Run gap detection
    detection_success = integrator.run_gap_detection()
    
    if detection_success:
        print("✅ Gap detection completed")
        
        # Get statistics
        stats = integrator.get_gap_statistics()
        
        print(f"\n📊 Gap Analysis Summary:")
        print(f"   Total gaps: {stats['total_gaps']}")
        print(f"   Pending research: {stats['pending_research']}")
        print(f"   Completed fills: {stats['completed_fills']}")
        print(f"   Completion rate: {stats['completion_rate']:.1%}")
        
        # Show pending requests
        pending_requests = integrator.check_pending_research_requests()
        
        if pending_requests:
            print(f"\n📋 {len(pending_requests)} research requests pending:")
            for req in pending_requests:
                gap_id = req['gap_id']
                queries = integrator.get_research_queries_for_gap(gap_id)
                print(f"   - {gap_id}: {len(queries)} queries ready")
            
            print(f"\n💡 To research gaps, call:")
            print(f"   perform_gap_research_with_ai('{pending_requests[0]['gap_id']}')")
        else:
            print("📊 No research requests pending")
        
        return {
            'success': True,
            'statistics': stats,
            'pending_requests': pending_requests
        }
    
    else:
        print("❌ Gap detection failed")
        return {
            'success': False,
            'error': 'Gap detection engine failed'
        }

if __name__ == "__main__":
    # Run gap detection and show pending research
    result = run_gap_detection_and_prepare_research()
    
    if result['success']:
        print("\n🎯 Cortex Gap Research Integration ready")
    else:
        print("\n❌ Gap Research Integration failed to initialize")
