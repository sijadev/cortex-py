#!/usr/bin/env python3
"""
Obsidian Integration for Cortex CLI
Intelligent extraction and synchronization of conversations into structured Obsidian notes
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiofiles

@dataclass
class ChatMessage:
    """Represents a single chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None
    message_id: Optional[str] = None

@dataclass
class ExtractedInsight:
    """Represents an insight extracted from chat"""
    insight_type: str  # 'decision', 'concept', 'action_item', 'code_pattern'
    content: str
    confidence: float
    related_topics: List[str]
    context: str

@dataclass
class ChatAnalysisResult:
    """Result of chat analysis"""
    topic: str
    summary: str
    key_insights: List[ExtractedInsight]
    decisions: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    code_snippets: List[Dict[str, Any]]
    related_concepts: List[str]
    obsidian_links: List[str]
    tags: List[str]
    duration_estimate: str
    word_count: int

class ChatContentExtractor:
    """Extracts structured information from chat conversations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Patterns for extracting different types of content
        self.decision_patterns = [
            r'(?i)(?:decided?|choosing|selected?|going with|will use|opted for)\s+(.+)',
            r'(?i)(?:the decision is|we\'ll|i\'ll)\s+(.+)',
            r'(?i)(?:solution|approach|strategy):\s*(.+)'
        ]
        
        self.action_patterns = [
            r'(?i)(?:need to|should|must|will|gonna|going to)\s+(.+)',
            r'(?i)(?:todo|action item|next step):\s*(.+)',
            r'(?i)(?:implement|create|build|add|fix)\s+(.+)'
        ]
        
        self.concept_patterns = [
            r'(?i)(?:this is about|focuses on|related to)\s+(.+)',
            r'(?i)(?:concept|idea|principle|pattern):\s*(.+)',
            r'(?i)(?:understanding|learning about)\s+(.+)'
        ]
        
        self.obsidian_link_pattern = r'\[\[([^\]]+)\]\]'
        self.code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        self.file_path_pattern = r'[/\\]?(?:[^/\\:*?"<>|\s]+[/\\])*[^/\\:*?"<>|\s]+\.[a-zA-Z0-9]+'
    
    def extract_chat_content(self, messages: List[ChatMessage], session_context: Optional[Dict] = None) -> ChatAnalysisResult:
        """Extract structured content from chat messages"""
        try:
            # Combine all message content
            full_text = ' '.join([msg.content for msg in messages])
            
            # Basic analysis
            word_count = len(full_text.split())
            estimated_duration = self._estimate_duration(len(messages))
            
            # Extract different types of content
            decisions = self._extract_decisions(messages)
            action_items = self._extract_action_items(messages)
            code_snippets = self._extract_code_snippets(messages)
            insights = self._extract_insights(messages)
            obsidian_links = self._extract_obsidian_links(full_text)
            related_concepts = self._extract_concepts(full_text)
            
            # Determine topic and generate summary
            topic = self._determine_topic(messages, session_context)
            summary = self._generate_summary(messages, decisions, action_items)
            tags = self._generate_tags(topic, decisions, action_items, code_snippets)
            
            return ChatAnalysisResult(
                topic=topic,
                summary=summary,
                key_insights=insights,
                decisions=decisions,
                action_items=action_items,
                code_snippets=code_snippets,
                related_concepts=related_concepts,
                obsidian_links=obsidian_links,
                tags=tags,
                duration_estimate=estimated_duration,
                word_count=word_count
            )
            
        except Exception as e:
            self.logger.error("Error extracting chat content: %s", e)
            return ChatAnalysisResult(
                topic="Chat Session",
                summary="Analysis failed",
                key_insights=[],
                decisions=[],
                action_items=[],
                code_snippets=[],
                related_concepts=[],
                obsidian_links=[],
                tags=['chat-session'],
                duration_estimate="Unknown",
                word_count=0
            )
    
    def _extract_decisions(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Extract decisions made during the conversation"""
        decisions = []
        
        for msg in messages:
            if msg.role == 'assistant':  # Decisions typically in assistant responses
                for pattern in self.decision_patterns:
                    matches = re.findall(pattern, msg.content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if len(match.strip()) > 10:  # Filter out very short matches
                            decisions.append({
                                'topic': self._extract_decision_topic(match),
                                'description': match.strip()[:200],
                                'rationale': self._extract_rationale(msg.content, match),
                                'timestamp': msg.timestamp,
                                'confidence': self._calculate_decision_confidence(match, msg.content)
                            })
        
        return decisions[:10]  # Limit to top 10 decisions
    
    def _extract_action_items(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Extract action items from the conversation"""
        action_items = []
        
        for msg in messages:
            for pattern in self.action_patterns:
                matches = re.findall(pattern, msg.content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if len(match.strip()) > 10:
                        action_items.append({
                            'description': match.strip()[:200],
                            'priority': self._determine_priority(match),
                            'source': msg.role,
                            'timestamp': msg.timestamp,
                            'completed': False,
                            'category': self._categorize_action(match)
                        })
        
        return action_items[:15]  # Limit to top 15 action items
    
    def _extract_code_snippets(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Extract code snippets and technical details"""
        code_snippets = []
        
        for msg in messages:
            # Extract code blocks
            code_blocks = re.findall(self.code_block_pattern, msg.content, re.DOTALL)
            for code in code_blocks:
                if len(code.strip()) > 20:  # Meaningful code blocks
                    language = self._detect_language(code)
                    code_snippets.append({
                        'code': code.strip()[:500],  # Limit code length
                        'language': language,
                        'context': self._extract_code_context(msg.content, code),
                        'source': msg.role,
                        'timestamp': msg.timestamp,
                        'type': self._classify_code_type(code)
                    })
            
            # Extract file paths
            file_paths = re.findall(self.file_path_pattern, msg.content)
            for file_path in file_paths:
                if len(file_path) > 5:  # Valid file paths
                    code_snippets.append({
                        'code': file_path,
                        'language': 'filepath',
                        'context': 'Referenced file',
                        'source': msg.role,
                        'timestamp': msg.timestamp,
                        'type': 'reference'
                    })
        
        return code_snippets[:20]  # Limit to top 20 snippets
    
    def _extract_insights(self, messages: List[ChatMessage]) -> List[ExtractedInsight]:
        """Extract key insights from the conversation"""
        insights = []
        
        for msg in messages:
            if msg.role == 'assistant':  # Focus on assistant insights
                # Look for conceptual explanations
                for pattern in self.concept_patterns:
                    matches = re.findall(pattern, msg.content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if len(match.strip()) > 15:
                            insights.append(ExtractedInsight(
                                insight_type='concept',
                                content=match.strip()[:200],
                                confidence=0.7,
                                related_topics=self._extract_related_topics(match),
                                context=msg.content[:100]
                            ))
        
        return insights[:10]
    
    def _extract_obsidian_links(self, text: str) -> List[str]:
        """Extract existing Obsidian links from text"""
        return re.findall(self.obsidian_link_pattern, text)
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract related concepts mentioned in the text"""
        # Simple keyword extraction - could be enhanced with NLP
        technical_terms = re.findall(r'\b[A-Z][a-zA-Z]+(?:[A-Z][a-z]*)*\b', text)  # CamelCase
        return list(set(technical_terms))[:10]
    
    def _determine_topic(self, messages: List[ChatMessage], session_context: Optional[Dict] = None) -> str:
        """Determine the main topic of the conversation"""
        if session_context and 'topic' in session_context:
            return session_context['topic']
        
        # Analyze first user message for topic hints
        if messages and messages[0].role == 'user':
            first_message = messages[0].content
            # Simple topic extraction from first message
            words = first_message.split()[:10]  # First 10 words
            return ' '.join(words).rstrip('.,!?') if words else "Chat Session"
        
        return "Chat Session"
    
    def _generate_summary(self, messages: List[ChatMessage], decisions: List[Dict], action_items: List[Dict]) -> str:
        """Generate a summary of the conversation"""
        summary_parts = []
        
        if messages:
            total_exchanges = len([m for m in messages if m.role == 'user'])
            summary_parts.append(f"Chat session with {total_exchanges} exchanges")
        
        if decisions:
            summary_parts.append(f"{len(decisions)} key decisions made")
        
        if action_items:
            summary_parts.append(f"{len(action_items)} action items identified")
        
        return '. '.join(summary_parts) + '.' if summary_parts else "Chat session summary"
    
    def _generate_tags(self, topic: str, decisions: List[Dict], action_items: List[Dict], code_snippets: List[Dict]) -> List[str]:
        """Generate appropriate tags for the conversation"""
        tags = ['chat-session']
        
        # Add topic-based tags
        topic_words = topic.lower().split()
        tags.extend([word for word in topic_words if len(word) > 3][:3])
        
        # Add content-based tags
        if decisions:
            tags.append('decisions')
        if action_items:
            tags.append('action-items')
        if code_snippets:
            tags.append('code')
            
            # Language-specific tags
            languages = set(snippet.get('language', '') for snippet in code_snippets)
            for lang in languages:
                if lang and lang != 'filepath':
                    tags.append(f'lang-{lang}')
        
        return list(set(tags))  # Remove duplicates
    
    def _estimate_duration(self, message_count: int) -> str:
        """Estimate conversation duration"""
        if message_count < 5:
            return "5-10 minutes"
        elif message_count < 15:
            return "10-30 minutes"
        elif message_count < 30:
            return "30-60 minutes"
        else:
            return "60+ minutes"
    
    def _extract_decision_topic(self, decision_text: str) -> str:
        """Extract topic from decision text"""
        words = decision_text.split()[:5]  # First 5 words
        return ' '.join(words).rstrip('.,!?')
    
    def _extract_rationale(self, full_content: str, decision: str) -> str:
        """Extract rationale for a decision"""
        decision_index = full_content.find(decision)
        if decision_index == -1:
            return ""
        
        rationale_patterns = [r'because (.+)', r'since (.+)', r'due to (.+)', r'as (.+)']
        context = full_content[max(0, decision_index-100):decision_index+200]
        
        for pattern in rationale_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)[:100]
        
        return ""
    
    def _calculate_decision_confidence(self, decision: str, context: str) -> float:
        """Calculate confidence score for a decision"""
        confidence_indicators = ['definitely', 'clearly', 'obviously', 'certainly']
        uncertainty_indicators = ['maybe', 'perhaps', 'might', 'could', 'possibly']
        
        decision_lower = decision.lower()
        context_lower = context.lower()
        
        confidence = 0.5
        
        for indicator in confidence_indicators:
            if indicator in decision_lower or indicator in context_lower:
                confidence += 0.1
        
        for indicator in uncertainty_indicators:
            if indicator in decision_lower or indicator in context_lower:
                confidence -= 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _determine_priority(self, action_text: str) -> str:
        """Determine priority of an action item"""
        high_priority_words = ['urgent', 'critical', 'important', 'asap', 'immediately']
        low_priority_words = ['later', 'eventually', 'someday', 'maybe', 'consider']
        
        action_lower = action_text.lower()
        
        if any(word in action_lower for word in high_priority_words):
            return 'high'
        elif any(word in action_lower for word in low_priority_words):
            return 'low'
        else:
            return 'medium'
    
    def _categorize_action(self, action_text: str) -> str:
        """Categorize the type of action"""
        code_words = ['implement', 'code', 'develop', 'program', 'fix', 'debug']
        research_words = ['research', 'investigate', 'study', 'analyze', 'explore']
        planning_words = ['plan', 'design', 'architect', 'organize', 'schedule']
        
        action_lower = action_text.lower()
        
        if any(word in action_lower for word in code_words):
            return 'development'
        elif any(word in action_lower for word in research_words):
            return 'research'
        elif any(word in action_lower for word in planning_words):
            return 'planning'
        else:
            return 'general'
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code snippet"""
        language_patterns = {
            'python': [r'def ', r'import ', r'from .+ import', r'print\(', r'if __name__'],
            'javascript': [r'function ', r'const ', r'let ', r'var ', r'=>', r'console\.log'],
            'java': [r'public class', r'private ', r'public static void main'],
            'cpp': [r'#include', r'using namespace', r'int main'],
            'html': [r'<html', r'<div', r'<p>', r'<script'],
            'css': [r'\{[^}]*\}', r'@media', r'\.class'],
            'sql': [r'SELECT ', r'FROM ', r'WHERE ', r'INSERT INTO'],
            'bash': [r'#!/bin/bash', r'echo ', r'cd ', r'ls '],
            'yaml': [r':\s*$', r'- ', r'version:'],
            'json': [r'^\s*\{', r':\s*"', r'^\s*\[']
        }
        
        code_lower = code.lower()
        
        for language, patterns in language_patterns.items():
            if any(re.search(pattern, code_lower, re.MULTILINE) for pattern in patterns):
                return language
        
        return 'text'
    
    def _extract_code_context(self, full_content: str, code: str) -> str:
        """Extract context around a code snippet"""
        code_index = full_content.find(code)
        if code_index == -1:
            return ""
        
        # Get text before the code block
        context_start = max(0, code_index - 100)
        context = full_content[context_start:code_index].strip()
        
        # Return last sentence or phrase
        sentences = re.split(r'[.!?]', context)
        return sentences[-1].strip() if sentences else ""
    
    def _classify_code_type(self, code: str) -> str:
        """Classify the type of code snippet"""
        if 'function' in code.lower() or 'def ' in code:
            return 'function'
        elif 'class' in code.lower():
            return 'class'
        elif 'import' in code.lower() or '#include' in code.lower():
            return 'imports'
        elif len(code.split('\n')) > 10:
            return 'complete_script'
        else:
            return 'snippet'
    
    def _extract_related_topics(self, content: str) -> List[str]:
        """Extract related topics from content"""
        # Simple extraction of capitalized words
        topics = re.findall(r'\b[A-Z][a-zA-Z]+\b', content)
        return list(set(topics))[:5]

class ObsidianNotesGenerator:
    """Generates structured Obsidian notes from chat analysis"""
    
    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path) if vault_path else Path.cwd() / "obsidian-vault"
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create vault structure
        self.chat_sessions_path = self.vault_path / "Chat-Sessions"
        self.decisions_path = self.vault_path / "Decisions"
        self.code_fragments_path = self.vault_path / "Code-Fragments"
        
        self._ensure_vault_structure()
    
    def _ensure_vault_structure(self):
        """Ensure Obsidian vault structure exists"""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.chat_sessions_path.mkdir(exist_ok=True)
        self.decisions_path.mkdir(exist_ok=True)
        self.code_fragments_path.mkdir(exist_ok=True)
    
    async def create_chat_note(self, analysis: ChatAnalysisResult, session_id: str = None) -> str:
        """Create a structured Obsidian note from chat analysis"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = re.sub(r'[^\w\s-]', '', analysis.topic)[:50]
            filename = f"{timestamp}_{safe_topic.replace(' ', '_')}.md"
            
            if session_id:
                filename = f"{timestamp}_{session_id}_{safe_topic.replace(' ', '_')}.md"
            
            note_path = self.chat_sessions_path / filename
            
            # Generate note content
            content = self._generate_note_content(analysis)
            
            # Write note
            async with aiofiles.open(note_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            self.logger.info("Created Obsidian note: %s", note_path.name)
            return str(note_path)
            
        except Exception as e:
            self.logger.error("Error creating chat note: %s", e)
            return ""
    
    def _generate_note_content(self, analysis: ChatAnalysisResult) -> str:
        """Generate formatted Obsidian note content"""
        lines = []
        
        # Frontmatter
        lines.append("---")
        lines.append(f"title: {analysis.topic}")
        lines.append(f"type: chat-session")
        lines.append(f"created: {datetime.now().isoformat()}")
        lines.append(f"duration: {analysis.duration_estimate}")
        lines.append(f"word_count: {analysis.word_count}")
        lines.append(f"tags: [{', '.join(analysis.tags)}]")
        lines.append("---")
        lines.append("")
        
        # Title
        lines.append(f"# {analysis.topic}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append(analysis.summary)
        lines.append("")
        
        # Key Insights
        if analysis.key_insights:
            lines.append("## Key Insights")
            for insight in analysis.key_insights:
                lines.append(f"- **{insight.insight_type.title()}**: {insight.content}")
                if insight.confidence < 0.8:
                    lines.append(f"  *Confidence: {insight.confidence:.1f}*")
            lines.append("")
        
        # Decisions
        if analysis.decisions:
            lines.append("## Decisions Made")
            for decision in analysis.decisions:
                lines.append(f"### {decision['topic']}")
                lines.append(f"**Decision**: {decision['description']}")
                if decision.get('rationale'):
                    lines.append(f"**Rationale**: {decision['rationale']}")
                lines.append(f"*Confidence: {decision.get('confidence', 0.5):.1f}*")
                lines.append("")
        
        # Action Items
        if analysis.action_items:
            lines.append("## Action Items")
            high_priority = [a for a in analysis.action_items if a.get('priority') == 'high']
            medium_priority = [a for a in analysis.action_items if a.get('priority') == 'medium']
            low_priority = [a for a in analysis.action_items if a.get('priority') == 'low']
            
            for priority, items in [('High', high_priority), ('Medium', medium_priority), ('Low', low_priority)]:
                if items:
                    lines.append(f"### {priority} Priority")
                    for item in items:
                        status = "☐" if not item.get('completed') else "✅"
                        lines.append(f"- {status} {item['description']} ({item.get('category', 'general')})")
                    lines.append("")
        
        # Code Snippets
        if analysis.code_snippets:
            lines.append("## Code Snippets")
            for snippet in analysis.code_snippets:
                if snippet.get('context'):
                    lines.append(f"### {snippet.get('context', 'Code Snippet')}")
                
                if snippet.get('language') != 'filepath':
                    lines.append(f"```{snippet.get('language', 'text')}")
                    lines.append(snippet['code'])
                    lines.append("```")
                else:
                    lines.append(f"**File**: `{snippet['code']}`")
                lines.append("")
        
        # Related Concepts
        if analysis.related_concepts:
            lines.append("## Related Concepts")
            for concept in analysis.related_concepts[:10]:
                lines.append(f"- [[{concept}]]")
            lines.append("")
        
        # Obsidian Links
        if analysis.obsidian_links:
            lines.append("## Linked Notes")
            for link in analysis.obsidian_links:
                lines.append(f"- [[{link}]]")
            lines.append("")
        
        return '\n'.join(lines)
    
    async def create_decision_notes(self, decisions: List[Dict[str, Any]]) -> List[str]:
        """Create separate decision notes"""
        decision_notes = []
        
        for decision in decisions:
            try:
                # Generate filename for decision
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_topic = re.sub(r'[^\w\s-]', '', decision['topic'])[:30]
                filename = f"ADR_{timestamp}_{safe_topic.replace(' ', '_')}.md"
                
                note_path = self.decisions_path / filename
                
                # Generate decision note content
                content = self._generate_decision_content(decision)
                
                # Write note
                async with aiofiles.open(note_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                
                decision_notes.append(str(note_path))
                
            except Exception as e:
                self.logger.error("Error creating decision note: %s", e)
        
        return decision_notes
    
    def _generate_decision_content(self, decision: Dict[str, Any]) -> str:
        """Generate decision note content in ADR format"""
        lines = []
        
        # Frontmatter
        lines.append("---")
        lines.append(f"title: {decision['topic']}")
        lines.append("type: decision")
        lines.append(f"status: decided")
        lines.append(f"created: {decision.get('timestamp', datetime.now().isoformat())}")
        lines.append(f"confidence: {decision.get('confidence', 0.5)}")
        lines.append("tags: [decision, adr]")
        lines.append("---")
        lines.append("")
        
        # ADR Format
        lines.append(f"# ADR: {decision['topic']}")
        lines.append("")
        
        lines.append("## Status")
        lines.append("Decided")
        lines.append("")
        
        lines.append("## Decision")
        lines.append(decision['description'])
        lines.append("")
        
        if decision.get('rationale'):
            lines.append("## Rationale")
            lines.append(decision['rationale'])
            lines.append("")
        
        lines.append("## Consequences")
        lines.append("*To be updated as implementation progresses*")
        lines.append("")
        
        return '\n'.join(lines)

class ObsidianSync:
    """Main Obsidian synchronization orchestrator"""
    
    def __init__(self, vault_path: str = None, workspace_path: str = None):
        self.vault_path = vault_path
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        
        self.extractor = ChatContentExtractor()
        self.notes_generator = ObsidianNotesGenerator(vault_path)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def sync_conversation(self, conversation_text: str, topic: str = None, create_decision_notes: bool = False) -> Dict[str, Any]:
        """Sync a conversation to Obsidian"""
        try:
            # Parse conversation into messages
            messages = self._parse_conversation(conversation_text)
            
            if not messages:
                return {'success': False, 'error': 'No messages found'}
            
            # Extract content
            session_context = {'topic': topic} if topic else None
            analysis = self.extractor.extract_chat_content(messages, session_context)
            
            # Create main chat note
            chat_note_path = await self.notes_generator.create_chat_note(analysis)
            
            result = {
                'success': True,
                'chat_note': chat_note_path,
                'analysis': {
                    'topic': analysis.topic,
                    'summary': analysis.summary,
                    'decisions_count': len(analysis.decisions),
                    'action_items_count': len(analysis.action_items),
                    'code_snippets_count': len(analysis.code_snippets),
                    'word_count': analysis.word_count,
                    'tags': analysis.tags
                }
            }
            
            # Optionally create separate decision notes
            if create_decision_notes and analysis.decisions:
                decision_notes = await self.notes_generator.create_decision_notes(analysis.decisions)
                result['decision_notes'] = decision_notes
            
            self.logger.info("Successfully synced conversation to Obsidian")
            return result
            
        except Exception as e:
            self.logger.error("Error syncing conversation: %s", e)
            return {'success': False, 'error': str(e)}
    
    def _parse_conversation(self, text: str) -> List[ChatMessage]:
        """Parse conversation text into structured messages"""
        messages = []
        lines = text.split('\n')
        
        current_role = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Detect role changes
            if line.lower().startswith(('user:', 'human:', 'you:')):
                # Save previous message
                if current_role and current_content:
                    messages.append(ChatMessage(
                        role=current_role,
                        content='\n'.join(current_content),
                        timestamp=datetime.now().isoformat()
                    ))
                
                # Start new user message
                current_role = 'user'
                current_content = [line[line.index(':') + 1:].strip()]
                
            elif line.lower().startswith(('assistant:', 'ai:', 'claude:', 'gpt:', 'bot:')):
                # Save previous message
                if current_role and current_content:
                    messages.append(ChatMessage(
                        role=current_role,
                        content='\n'.join(current_content),
                        timestamp=datetime.now().isoformat()
                    ))
                
                # Start new assistant message
                current_role = 'assistant'
                current_content = [line[line.index(':') + 1:].strip()]
                
            elif current_role and line:
                current_content.append(line)
        
        # Add final message
        if current_role and current_content:
            messages.append(ChatMessage(
                role=current_role,
                content='\n'.join(current_content),
                timestamp=datetime.now().isoformat()
            ))
        
        return messages
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """Get statistics about the Obsidian vault"""
        try:
            stats = {
                'vault_path': str(self.notes_generator.vault_path),
                'vault_exists': self.notes_generator.vault_path.exists(),
                'chat_sessions': 0,
                'decisions': 0,
                'code_fragments': 0
            }
            
            if stats['vault_exists']:
                # Count files in each directory
                if self.notes_generator.chat_sessions_path.exists():
                    stats['chat_sessions'] = len(list(self.notes_generator.chat_sessions_path.glob('*.md')))
                
                if self.notes_generator.decisions_path.exists():
                    stats['decisions'] = len(list(self.notes_generator.decisions_path.glob('*.md')))
                
                if self.notes_generator.code_fragments_path.exists():
                    stats['code_fragments'] = len(list(self.notes_generator.code_fragments_path.glob('*.md')))
            
            return stats
            
        except Exception as e:
            self.logger.error("Error getting vault stats: %s", e)
            return {'error': str(e)}
