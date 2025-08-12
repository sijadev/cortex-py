#!/usr/bin/env python3
"""
Chat-to-Obsidian Sync - Intelligent extraction and synchronization of chat sessions
Converts Claude Code conversations into structured Obsidian notes with automatic linking
"""

import json
import re
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import Counter
import hashlib

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
            user_messages = [msg for msg in messages if msg.role == 'user']
            assistant_messages = [msg for msg in messages if msg.role == 'assistant']
            
            # Basic analysis
            word_count = len(full_text.split())
            estimated_duration = self._estimate_duration(len(messages), word_count)
            
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
            self.logger.error(f"Error extracting chat content: {e}")
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
                        'type': 'file_reference'
                    })
        
        return code_snippets[:20]  # Limit to top 20 snippets
    
    def _extract_insights(self, messages: List[ChatMessage]) -> List[ExtractedInsight]:
        """Extract key insights from the conversation"""
        insights = []
        
        for msg in messages:
            if msg.role == 'assistant':  # Insights usually from assistant
                content = msg.content.lower()
                
                # Look for insight indicators
                insight_indicators = [
                    'important to note', 'key point', 'crucial', 'significant',
                    'worth noting', 'interesting', 'benefit', 'advantage',
                    'best practice', 'recommendation', 'approach', 'strategy'
                ]
                
                for indicator in insight_indicators:
                    if indicator in content:
                        # Extract sentence containing the indicator
                        sentences = re.split(r'[.!?]+', msg.content)
                        for sentence in sentences:
                            if indicator in sentence.lower() and len(sentence.strip()) > 30:
                                insights.append(ExtractedInsight(
                                    insight_type='general',
                                    content=sentence.strip()[:300],
                                    confidence=0.7,
                                    related_topics=self._extract_topics_from_text(sentence),
                                    context=f"From assistant response about {indicator}"
                                ))
        
        return insights[:10]  # Limit to top 10 insights
    
    def _extract_obsidian_links(self, text: str) -> List[str]:
        """Extract Obsidian-style links from text"""
        links = re.findall(self.obsidian_link_pattern, text)
        return list(set(links))  # Remove duplicates
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from the conversation"""
        # Simple concept extraction based on technical terms and patterns
        technical_terms = [
            'api', 'database', 'algorithm', 'pattern', 'architecture', 'framework',
            'library', 'service', 'module', 'component', 'interface', 'protocol',
            'authentication', 'authorization', 'validation', 'optimization',
            'deployment', 'testing', 'debugging', 'monitoring', 'logging'
        ]
        
        found_concepts = []
        text_lower = text.lower()
        
        for term in technical_terms:
            if term in text_lower:
                found_concepts.append(term)
        
        # Extract capitalized terms (likely proper nouns/concepts)
        capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', text)
        found_concepts.extend([term for term in capitalized_terms if len(term) > 3])
        
        return list(set(found_concepts))[:20]  # Remove duplicates and limit
    
    def _determine_topic(self, messages: List[ChatMessage], context: Optional[Dict]) -> str:
        """Determine the main topic of the conversation"""
        if context and 'topic' in context:
            return context['topic']
        
        # Analyze first few messages for topic
        first_messages = messages[:3]
        combined_text = ' '.join([msg.content for msg in first_messages])
        
        # Look for topic indicators
        if 'obsidian' in combined_text.lower():
            return 'Obsidian Integration'
        elif 'test' in combined_text.lower():
            return 'Testing & Development'
        elif 'implement' in combined_text.lower() or 'code' in combined_text.lower():
            return 'Implementation Discussion'
        elif 'error' in combined_text.lower() or 'bug' in combined_text.lower():
            return 'Debugging & Troubleshooting'
        elif 'design' in combined_text.lower() or 'architecture' in combined_text.lower():
            return 'System Design'
        else:
            return 'General Discussion'
    
    def _generate_summary(self, messages: List[ChatMessage], decisions: List[Dict], action_items: List[Dict]) -> str:
        """Generate a summary of the conversation"""
        summary_parts = []
        
        if decisions:
            summary_parts.append(f"Made {len(decisions)} key decision(s)")
        
        if action_items:
            summary_parts.append(f"identified {len(action_items)} action item(s)")
        
        # Analyze conversation flow
        user_questions = sum(1 for msg in messages if msg.role == 'user' and '?' in msg.content)
        if user_questions > 0:
            summary_parts.append(f"addressed {user_questions} question(s)")
        
        if not summary_parts:
            summary_parts.append("discussed various topics")
        
        return f"Conversation that {', '.join(summary_parts)}."
    
    def _generate_tags(self, topic: str, decisions: List[Dict], action_items: List[Dict], code_snippets: List[Dict]) -> List[str]:
        """Generate relevant tags for the conversation"""
        tags = ['chat-session', 'claude-ai']
        
        # Add topic-based tags
        topic_words = topic.lower().split()
        tags.extend([word.replace(' ', '-') for word in topic_words if len(word) > 2])
        
        # Add content-based tags
        if decisions:
            tags.append('decisions')
        if action_items:
            tags.append('action-items')
        if code_snippets:
            tags.append('code')
            
            # Add language-specific tags
            languages = set(snippet.get('language', '') for snippet in code_snippets)
            tags.extend([lang for lang in languages if lang and lang != 'filepath'])
        
        return list(set(tags))  # Remove duplicates
    
    def _estimate_duration(self, message_count: int, word_count: int) -> str:
        """Estimate conversation duration based on message count and words"""
        # Rough estimation: 150 words per minute reading, plus interaction time
        reading_time = word_count / 150
        interaction_time = message_count * 0.5  # 30 seconds per message exchange
        total_minutes = reading_time + interaction_time
        
        if total_minutes < 1:
            return "< 1 minute"
        elif total_minutes < 60:
            return f"~{int(total_minutes)} minutes"
        else:
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            return f"~{hours}h {minutes}m"
    
    def _extract_decision_topic(self, decision_text: str) -> str:
        """Extract the main topic of a decision"""
        words = decision_text.split()[:5]  # First 5 words
        return ' '.join(words).rstrip('.,!?')
    
    def _extract_rationale(self, full_content: str, decision: str) -> str:
        """Extract rationale for a decision"""
        # Look for explanatory text near the decision
        decision_index = full_content.find(decision)
        if decision_index == -1:
            return ""
        
        # Look for rationale indicators
        rationale_patterns = [r'because (.+)', r'since (.+)', r'due to (.+)', r'as (.+)']
        
        context = full_content[max(0, decision_index-100):decision_index+200]
        
        for pattern in rationale_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)[:100]  # Limit length
        
        return ""
    
    def _calculate_decision_confidence(self, decision: str, context: str) -> float:
        """Calculate confidence score for a decision"""
        confidence_indicators = ['definitely', 'clearly', 'obviously', 'certainly']
        uncertainty_indicators = ['maybe', 'perhaps', 'might', 'could', 'possibly']
        
        decision_lower = decision.lower()
        context_lower = context.lower()
        
        confidence = 0.5  # Base confidence
        
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
        action_lower = action_text.lower()
        
        if any(word in action_lower for word in ['test', 'debug', 'fix']):
            return 'testing'
        elif any(word in action_lower for word in ['implement', 'code', 'develop']):
            return 'development'
        elif any(word in action_lower for word in ['research', 'investigate', 'study']):
            return 'research'
        elif any(word in action_lower for word in ['document', 'write', 'note']):
            return 'documentation'
        else:
            return 'general'
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language of code snippet"""
        code_lower = code.lower()
        
        if 'def ' in code or 'import ' in code or 'python' in code_lower:
            return 'python'
        elif '{' in code and '}' in code and ('function' in code or '=>' in code):
            return 'javascript'
        elif '#!/usr/bin/env python' in code:
            return 'python'
        elif 'function' in code and '{' in code:
            return 'javascript'
        elif 'public class' in code or 'System.out' in code:
            return 'java'
        elif '#include' in code or 'int main' in code:
            return 'cpp'
        elif 'SELECT' in code.upper() or 'FROM' in code.upper():
            return 'sql'
        elif '<' in code and '>' in code and 'html' in code_lower:
            return 'html'
        else:
            return 'unknown'
    
    def _extract_code_context(self, full_content: str, code: str) -> str:
        """Extract context around a code snippet"""
        code_index = full_content.find(code)
        if code_index == -1:
            return "Code snippet"
        
        # Get text before the code block
        before_text = full_content[max(0, code_index-100):code_index].strip()
        sentences = before_text.split('.')
        if sentences:
            return sentences[-1].strip()[:50] if sentences[-1].strip() else "Code snippet"
        
        return "Code snippet"
    
    def _classify_code_type(self, code: str) -> str:
        """Classify the type of code snippet"""
        code_lower = code.lower()
        
        if 'class' in code_lower and 'def' in code_lower:
            return 'class_definition'
        elif 'def ' in code_lower or 'function' in code_lower:
            return 'function'
        elif 'import' in code_lower:
            return 'import_statement'
        elif 'test' in code_lower and 'assert' in code_lower:
            return 'test_code'
        elif any(word in code_lower for word in ['select', 'insert', 'update', 'delete']):
            return 'sql_query'
        elif '#!/' in code:
            return 'script'
        else:
            return 'code_snippet'
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract topics from a piece of text"""
        # Simple topic extraction - could be enhanced with NLP
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        common_words = ['that', 'this', 'with', 'have', 'will', 'been', 'from', 'they', 'them', 'were', 'said']
        topics = [word for word in words if word not in common_words]
        return topics[:5]  # Limit to 5 topics

class ChatObsidianSyncer:
    """Syncs chat analysis results to Obsidian"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.extractor = ChatContentExtractor()
    
    async def sync_chat_session(self, messages: List[ChatMessage], session_context: Optional[Dict] = None) -> bool:
        """Sync a chat session to Obsidian"""
        try:
            from obsidian_mcp_bridge import ObsidianMCPBridge
            
            # Extract chat content
            analysis = self.extractor.extract_chat_content(messages, session_context)
            
            # Prepare chat data for bridge
            chat_data = {
                'topic': analysis.topic,
                'summary': analysis.summary,
                'messages': [asdict(msg) for msg in messages[-10:]],  # Last 10 messages
                'extracted_insights': [asdict(insight) for insight in analysis.key_insights],
                'decisions': analysis.decisions,
                'action_items': analysis.action_items,
                'related_notes': analysis.obsidian_links,
                'tags': analysis.tags,
                'duration': analysis.duration_estimate,
                'word_count': analysis.word_count,
                'session_id': session_context.get('session_id', 'unknown') if session_context else 'unknown',
                'model': 'Claude Code'
            }
            
            # Use MCP bridge to sync
            bridge = ObsidianMCPBridge()
            success, result = await bridge.sync_chat_session(chat_data)
            
            if success:
                self.logger.info(f"Successfully synced chat session: {result}")
                
                # Also create related notes for significant decisions and action items
                await self._create_related_notes(analysis, bridge)
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error syncing chat session: {e}")
            return False
    
    async def _create_related_notes(self, analysis: ChatAnalysisResult, bridge):
        """Create related notes for significant decisions and action items"""
        try:
            # Create ADR for major decisions
            major_decisions = [d for d in analysis.decisions if d.get('confidence', 0) > 0.7]
            for decision in major_decisions[:3]:  # Limit to top 3
                adr_data = {
                    'topic': f"ADR - {decision['topic']}",
                    'summary': f"Decision: {decision['description']}",
                    'findings': [f"Rationale: {decision.get('rationale', 'Not specified')}"],
                    'related_concepts': analysis.related_concepts[:5],
                    'cross_vault_connections': [],
                    'tags': ['adr', 'decision', 'chat-derived'] + analysis.tags[:3],
                    'source_vaults': ['chat-session'],
                    'correlation_count': 1,
                    'confidence': decision.get('confidence', 0.5)
                }
                
                await bridge.create_cortex_insight_note(adr_data)
            
            # Create code fragment notes for significant code snippets
            significant_code = [c for c in analysis.code_snippets if c.get('type') != 'file_reference' and len(c.get('code', '')) > 50]
            for code_snippet in significant_code[:2]:  # Limit to top 2
                code_data = {
                    'topic': f"Code Fragment - {code_snippet.get('language', 'Unknown').title()}",
                    'summary': f"Code from chat: {code_snippet.get('context', 'Code snippet')}",
                    'findings': [f"Language: {code_snippet.get('language', 'unknown')}", f"Type: {code_snippet.get('type', 'unknown')}"],
                    'related_concepts': [code_snippet.get('language', 'code')],
                    'cross_vault_connections': [],
                    'tags': ['code-fragment', 'chat-derived', code_snippet.get('language', 'code')] + analysis.tags[:2],
                    'source_vaults': ['chat-session'],
                    'correlation_count': 1,
                    'confidence': 0.6
                }
                
                await bridge.create_cortex_insight_note(code_data)
                
        except Exception as e:
            self.logger.warning(f"Error creating related notes: {e}")

# Utility functions for integration
def create_chat_messages_from_text(conversation_text: str) -> List[ChatMessage]:
    """Convert conversation text to ChatMessage objects"""
    messages = []
    
    # Simple parsing - assumes conversation format like "User: ...", "Assistant: ..."
    lines = conversation_text.split('\n')
    current_role = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('User:') or line.startswith('Human:'):
            if current_role and current_content:
                messages.append(ChatMessage(
                    role=current_role,
                    content='\n'.join(current_content),
                    timestamp=datetime.now().isoformat()
                ))
            current_role = 'user'
            current_content = [line[line.index(':') + 1:].strip()]
        elif line.startswith('Assistant:') or line.startswith('Claude:'):
            if current_role and current_content:
                messages.append(ChatMessage(
                    role=current_role,
                    content='\n'.join(current_content),
                    timestamp=datetime.now().isoformat()
                ))
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

async def sync_current_chat_to_obsidian(conversation_text: str, topic: str = "Chat Session") -> bool:
    """Sync current chat conversation to Obsidian"""
    try:
        messages = create_chat_messages_from_text(conversation_text)
        if not messages:
            logging.warning("No messages found in conversation text")
            return False
        
        session_context = {
            'topic': topic,
            'session_id': hashlib.md5(conversation_text.encode()).hexdigest()[:8]
        }
        
        syncer = ChatObsidianSyncer()
        result = await syncer.sync_chat_session(messages, session_context)
        
        return result
        
    except Exception as e:
        logging.error(f"Error syncing current chat: {e}")
        return False

if __name__ == "__main__":
    # Test the chat extraction and sync
    import sys
    import asyncio
    
    async def test_chat_sync(conversation_text=None, topic="Chat Sync Test"):
        if conversation_text is None:
            print("❌ No conversation text provided")
            print("Usage: python chat_obsidian_sync.py 'User: Hello\\nAssistant: Hi there!' 'Test Topic'")
            return False
        
        # Test the sync
        result = await sync_current_chat_to_obsidian(conversation_text, topic)
        print(f"✅ Chat sync test result: {result}")
        return result
    
    # Parse command line arguments
    if len(sys.argv) >= 2:
        conversation = sys.argv[1]
        topic = sys.argv[2] if len(sys.argv) >= 3 else "Command Line Chat Test"
        asyncio.run(test_chat_sync(conversation, topic))
    else:
        asyncio.run(test_chat_sync())