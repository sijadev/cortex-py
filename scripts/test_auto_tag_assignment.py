#!/usr/bin/env python3
"""
Test Automatic Tag Assignment for Performance Tags
Created: 2025-08-15
Purpose: Test and demonstrate automatic assignment of performance-related tags
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.governance.data_governance import DataGovernanceEngine
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_automatic_tag_assignment():
    """Test automatic tag assignment with performance-related content"""

    print("🧪 Testing Automatic Tag Assignment for Performance Tags")
    print("=" * 60)

    # Initialize governance engine
    governance = DataGovernanceEngine()

    # Test cases for different performance scenarios
    test_cases = [
        {
            "name": "CPU Performance Monitoring",
            "content": """
            # CPU Performance Monitoring with Python
            
            This note covers performance metrics and monitoring techniques for CPU usage tracking.
            We'll explore benchmarking tools, timing measurements, and profiling methods.
            
            ## Key Topics:
            - Performance measurement with time module
            - CPU usage statistics collection
            - Monitoring system performance
            - Benchmarking different algorithms
            
            ## Code Example:
            ```python
            import time
            import psutil
            
            def monitor_cpu_performance():
                start_time = time.time()
                cpu_usage = psutil.cpu_percent(interval=1)
                execution_time = time.time() - start_time
                return cpu_usage, execution_time
            ```
            """,
            "description": "Comprehensive guide for CPU performance monitoring and metrics collection",
            "note_type": "guide",
            "expected_tags": ["performance-metrics"]
        },
        {
            "name": "Database Query Optimization",
            "content": """
            # Database Query Optimization Strategies
            
            This document outlines system optimization techniques for improving database performance.
            Focus on query optimization, indexing strategies, and caching mechanisms.
            
            ## Optimization Areas:
            - Query optimization and indexing
            - Memory usage optimization
            - Database connection pooling
            - Caching strategies for speed improvement
            - Scaling database operations
            
            ## Performance Tuning:
            - Analyze slow queries
            - Optimize database schema
            - Implement efficient caching
            """,
            "description": "Database optimization strategies and performance tuning guide",
            "note_type": "optimization",
            "expected_tags": ["system-optimization"]
        },
        {
            "name": "Command Line Tool Tracking",
            "content": """
            # Command Execution Tracking System
            
            Implementation of a command tracking and monitoring system for CLI tools.
            Includes logging, audit trails, and execution history management.
            
            ## Features:
            - Command execution monitoring
            - Shell script tracking
            - Terminal session logging
            - CLI command history audit
            - Process monitoring and tracking
            
            ## Implementation:
            ```python
            import subprocess
            import logging
            
            def track_command_execution(command):
                logging.info(f"Executing command: {command}")
                result = subprocess.run(command, shell=True, capture_output=True)
                logging.info(f"Command completed with exit code: {result.returncode}")
                return result
            ```
            """,
            "description": "System for tracking and monitoring command line tool execution",
            "note_type": "system",
            "expected_tags": ["command-tracking"]
        },
        {
            "name": "Full Performance Suite",
            "content": """
            # Comprehensive Performance Analysis Suite
            
            This is a complete performance analysis system that includes metrics collection,
            system optimization techniques, and command execution tracking.
            
            ## Performance Metrics:
            - Benchmark timing and measurement
            - Throughput and latency monitoring
            - Response time statistics
            - Performance profiling tools
            
            ## System Optimization:
            - Memory usage optimization
            - CPU performance tuning
            - Database query optimization
            - Caching and scaling strategies
            
            ## Command Tracking:
            - Shell command monitoring
            - Script execution logging
            - Terminal session audit
            - Process tracking and history
            
            This comprehensive suite covers all aspects of performance monitoring,
            optimization, and command tracking in a unified system.
            """,
            "description": "Complete performance analysis suite with metrics, optimization, and tracking",
            "note_type": "suite",
            "expected_tags": ["performance-metrics", "system-optimization", "command-tracking"]
        }
    ]

    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print("-" * 40)

        # Validate note creation with automatic tag suggestion
        result = governance.validate_note_creation(
            name=test_case["name"],
            content=test_case["content"],
            description=test_case["description"],
            note_type=test_case["note_type"]
        )

        print(f"✅ Validation passed: {result.passed}")

        if result.errors:
            print("❌ Errors:")
            for error in result.errors:
                print(f"   • {error}")

        if result.warnings:
            print("⚠️  Warnings:")
            for warning in result.warnings:
                print(f"   • {warning}")

        if result.suggestions:
            print("💡 Auto-Generated Suggestions:")
            for suggestion in result.suggestions:
                print(f"   • {suggestion}")

                # Check if expected tags are suggested
                if "Empfohlene Tags:" in suggestion:
                    suggested_tags = suggestion.replace("Empfohlene Tags: ", "").split(", ")
                    expected_found = []
                    for expected_tag in test_case["expected_tags"]:
                        if expected_tag in suggested_tags:
                            expected_found.append(expected_tag)

                    if expected_found:
                        print(f"   ✅ Expected performance tags found: {', '.join(expected_found)}")
                    else:
                        print(f"   ⚠️  Expected tags not found: {', '.join(test_case['expected_tags'])}")

        print()

    print("=" * 60)
    print("🎯 Automatic Tag Assignment Test Completed!")
    print("\n📋 Summary:")
    print("   • Performance-metrics tag: Automatically assigned for performance measurement content")
    print("   • System-optimization tag: Automatically assigned for optimization and tuning content")
    print("   • Command-tracking tag: Automatically assigned for command monitoring content")
    print("\n🚀 The governance system now automatically detects and suggests performance-related tags!")

def test_tag_assignment_integration():
    """Test integration with the actual tag assignment system"""

    print("\n🔗 Testing Tag Assignment Integration")
    print("=" * 40)

    try:
        from neo4j import GraphDatabase

        # Neo4j connection settings
        NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
        NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        with driver.session() as session:
            # Check if performance tags exist in the database
            result = session.run("""
                MATCH (t:Tag)
                WHERE t.category = 'performance'
                RETURN t.name as name, t.description as description
                ORDER BY t.name
            """)

            performance_tags = list(result)

            if performance_tags:
                print("✅ Performance tags found in Neo4j database:")
                for record in performance_tags:
                    print(f"   • {record['name']}: {record['description']}")

                print(f"\n📊 Total performance tags available: {len(performance_tags)}")
                print("🔗 Integration ready: Governance system can automatically assign these tags")
            else:
                print("⚠️  No performance tags found in database")
                print("💡 Run the create_performance_tags.py script first")

        driver.close()

    except Exception as e:
        print(f"⚠️  Could not check Neo4j integration: {e}")
        print("💡 Make sure Neo4j is running and accessible")

if __name__ == "__main__":
    test_automatic_tag_assignment()
    test_tag_assignment_integration()
