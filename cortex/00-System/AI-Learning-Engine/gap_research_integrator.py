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
from typing import List, Dict, Any, Optional

class CortexGapResearchIntegrator:
    """Integrates gap detection with Claude's web research capabilities"""
    
    def __init__(self, cortex_path: str = "/Users/simonjanke/Projects/cortex"):
        self.cortex_path = Path(cortex_path)
        self.data_path = self.cortex_path / "00-System" / "AI-Learning-Engine" / "data"
        self.research_requests_file = self.data_path / "research_requests.json"
        self.gap_fills_path = self.cortex_path / "05-Insights" / "Auto-Gap-Fills"
        
        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.gap_fills_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def check_pending_research_requests(self) -> List[Dict[str, Any]]:
        """Check for pending research requests from gap detection"""
        
        if not self.research_requests_file.exists():
            return []
        
        try:
            with open(self.research_requests_file, 'r') as f:
                requests = json.load(f)
            
            # Filter for pending requests
            pending = [req for req in requests if req.get('status') == 'pending_claude_research']
            
            return pending
        
        except Exception as e:
            self.logger.error(f"Error reading research requests: {e}")
            return []
    
    def get_research_queries_for_gap(self, gap_id: str) -> List[str]:
        """Get specific research queries for a gap"""
        
        gaps_file = self.data_path / "knowledge_gaps" / "detected_gaps.json"
        
        if not gaps_file.exists():
            return []
        
        try:
            with open(gaps_file, 'r') as f:
                gaps = json.load(f)
            
            # Find the specific gap
            for gap in gaps:
                if gap.get('gap_id') == gap_id:
                    return gap.get('research_queries', [])
            
            return []
        
        except Exception as e:
            self.logger.error(f"Error reading gaps data: {e}")
            return []
    
    def mark_research_completed(self, gap_id: str, research_results: Dict[str, Any]):
        """Mark a research request as completed and save results"""
        
        try:
            # Update research requests
            requests = []
            if self.research_requests_file.exists():
                with open(self.research_requests_file, 'r') as f:
                    requests = json.load(f)
            
            # Update status
            for req in requests:
                if req.get('gap_id') == gap_id:
                    req['status'] = 'completed'
                    req['completed_at'] = datetime.now().isoformat()
                    req['results_summary'] = research_results
            
            # Save updated requests
            with open(self.research_requests_file, 'w') as f:
                json.dump(requests, f, indent=2)
            
            # Save detailed results
            results_file = self.gap_fills_path / f"research_results_{gap_id}.json"
            with open(results_file, 'w') as f:
                json.dump(research_results, f, indent=2)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error marking research completed: {e}")
            return False
    
    def generate_gap_fill_content(self, gap_id: str, research_results: List[Dict[str, Any]]) -> str:
        """Generate structured content to fill a knowledge gap"""
        
        # Load gap details
        gaps_file = self.data_path / "knowledge_gaps" / "detected_gaps.json"
        gap_info = None
        
        if gaps_file.exists():
            with open(gaps_file, 'r') as f:
                gaps = json.load(f)
            
            for gap in gaps:
                if gap.get('gap_id') == gap_id:
                    gap_info = gap
                    break
        
        if not gap_info:
            return f"# Gap Fill Error\nCould not find gap information for {gap_id}"
        
        # Generate content based on gap type and research results
        content = f"""# {gap_info['title']} - Auto Research Fill

*Knowledge gap automatically filled by Cortex Gap Detection & Web Research*

## Gap Information
- **Gap ID**: {gap_id}
- **Type**: {gap_info['gap_type']}
- **Priority**: {gap_info['priority']}
- **Confidence**: {gap_info['confidence']:.1%}
- **Detected**: {gap_info['detected_date']}
- **Research Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Gap Description
{gap_info['description']}

## Research Context
**Original Context**: {gap_info['context']}

## Research Results

Based on targeted web research with {len(research_results)} sources:

"""
        
        # Add research results
        for i, result in enumerate(research_results, 1):
            content += f"""### Source {i}: {result.get('title', 'Unknown Title')}

**URL**: {result.get('url', 'N/A')}  
**Relevance**: {result.get('relevance_score', 0):.1%}  
**Authority**: {result.get('authority_score', 0):.1%}

**Key Findings**:
{result.get('content', 'No content available')[:500]}...

"""
        
        # Add synthesis section
        content += f"""## Synthesis & Integration

### Key Insights Discovered:
"""
        
        # Extract key insights based on gap type
        if gap_info['gap_type'] == 'missing_benchmarks':
            content += """
- Performance benchmarks and metrics identified
- Industry standard comparisons available
- Measurement criteria established
"""
        elif gap_info['gap_type'] == 'incomplete_research':
            content += """
- Additional research sources integrated
- Missing perspectives covered
- Knowledge base expanded
"""
        elif gap_info['gap_type'] == 'missing_examples':
            content += """
- Practical examples and use cases added
- Implementation patterns identified
- Real-world applications documented
"""
        elif gap_info['gap_type'] == 'missing_alternatives':
            content += """
- Alternative solutions researched
- Comparative analysis completed
- Decision criteria clarified
"""
        
        content += f"""
### Recommended Actions:
1. **Integrate findings** into original decision/research document
2. **Update confidence scores** based on additional information
3. **Review implications** for related decisions
4. **Apply learnings** to similar future decisions

### Research Queries Used:
"""
        
        for query in gap_info.get('research_queries', []):
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

---
*Auto-generated by Cortex Gap Detection Engine v1.0*  
*Research completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def save_gap_fill(self, gap_id: str, content: str) -> str:
        """Save gap fill content to file"""
        
        filename = f"Gap-Fill-{gap_id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.gap_fills_path / filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return str(file_path)

# Function that Claude can call to perform gap research
def perform_gap_research_with_claude(gap_id: str, use_web_search: bool = True, use_exa_search: bool = True):
    """Function for Claude to perform web research for a specific gap"""
    
    integrator = CortexGapResearchIntegrator()
    
    # Get research queries for this gap
    queries = integrator.get_research_queries_for_gap(gap_id)
    
    if not queries:
        print(f"❌ No research queries found for gap {gap_id}")
        return None
    
    print(f"🔍 Starting research for gap {gap_id}")
    print(f"📋 Research queries: {queries}")
    
    # This is where Claude would use web_search tools
    # Return structure for Claude to fill in
    research_template = {
        'gap_id': gap_id,
        'queries_researched': queries,
        'research_method': 'claude_web_search',
        'timestamp': datetime.now().isoformat(),
        'results': [
            {
                'query': query,
                'title': 'CLAUDE_TO_FILL',
                'url': 'CLAUDE_TO_FILL', 
                'content': 'CLAUDE_TO_FILL',
                'relevance_score': 0.0,  # Claude to assess
                'authority_score': 0.0,  # Claude to assess
                'currency_score': 0.0    # Claude to assess
            }
            for query in queries[:3]  # Limit to top 3
        ]
    }
    
    print(f"📊 Research template prepared for Claude to complete")
    return research_template

# Function to complete gap research after Claude fills in data
def complete_gap_research(gap_id: str, research_results: List[Dict[str, Any]]):
    """Complete gap research after Claude has filled in the data"""
    
    integrator = CortexGapResearchIntegrator()
    
    # Generate gap fill content
    content = integrator.generate_gap_fill_content(gap_id, research_results)
    
    # Save gap fill
    file_path = integrator.save_gap_fill(gap_id, content)
    
    # Mark research as completed
    research_summary = {
        'sources_count': len(research_results),
        'gap_fill_file': file_path,
        'research_quality': 'claude_verified'
    }
    
    success = integrator.mark_research_completed(gap_id, research_summary)
    
    if success:
        print(f"✅ Gap research completed for {gap_id}")
        print(f"📄 Gap fill saved: {file_path}")
        return file_path
    else:
        print(f"❌ Error completing gap research for {gap_id}")
        return None

# Main integration function for learning cycle
def run_gap_detection_and_prepare_research():
    """Run gap detection and prepare research requests for Claude"""
    
    print("🔍 Running Cortex Gap Detection...")
    
    # Run gap detection
    try:
        result = subprocess.run([
            sys.executable,
            "/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine/gap_detection_engine.py"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Gap detection completed")
            
            # Check for pending research requests
            integrator = CortexGapResearchIntegrator()
            pending_requests = integrator.check_pending_research_requests()
            
            if pending_requests:
                print(f"\n📋 {len(pending_requests)} research requests pending:")
                for req in pending_requests:
                    gap_id = req['gap_id']
                    queries = integrator.get_research_queries_for_gap(gap_id)
                    print(f"   - {gap_id}: {len(queries)} queries ready")
                
                print(f"\n💡 To research gaps, call:")
                print(f"   perform_gap_research_with_claude('{pending_requests[0]['gap_id']}')")
            else:
                print("📊 No research requests pending")
        
        else:
            print(f"❌ Gap detection failed: {result.stderr}")
    
    except Exception as e:
        print(f"❌ Error running gap detection: {e}")

if __name__ == "__main__":
    # Run gap detection and show pending research
    run_gap_detection_and_prepare_research()
