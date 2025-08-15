#!/usr/bin/env python3
"""
Create Performance Tags for Cortex System
Created: 2025-08-15
Purpose: Create specific tags for performance-related notes
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase
import logging

# Configuration
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neo4jtest")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_performance_tags():
    """Create performance-related tags in the Neo4j database"""

    # Define the performance tags to create
    performance_tags = [
        {
            "name": "performance-metrics",
            "description": "Tag for notes related to performance measurements and metrics",
            "category": "performance"
        },
        {
            "name": "system-optimization",
            "description": "Tag for notes about system optimization techniques and improvements",
            "category": "performance"
        },
        {
            "name": "command-tracking",
            "description": "Tag for notes related to command execution tracking and monitoring",
            "category": "performance"
        }
    ]

    driver = None
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        with driver.session() as session:
            # Create each performance tag
            for tag_info in performance_tags:
                # Create tag with properties
                result = session.run("""
                    MERGE (t:Tag {name: $name})
                    SET t.description = $description,
                        t.category = $category,
                        t.created_at = datetime(),
                        t.created_by = 'performance_tag_script'
                    RETURN t.name as name
                """,
                name=tag_info["name"],
                description=tag_info["description"],
                category=tag_info["category"]
                )

                # Verify tag was created
                tag_record = result.single()
                if tag_record:
                    logger.info(f"✅ Created performance tag: '{tag_record['name']}'")
                    print(f"✅ Created performance tag: '{tag_record['name']}'")
                    print(f"   📝 Description: {tag_info['description']}")
                else:
                    logger.warning(f"⚠️  Tag '{tag_info['name']}' may already exist")
                    print(f"⚠️  Tag '{tag_info['name']}' may already exist")

            # Verify all tags were created by counting them
            count_result = session.run("""
                MATCH (t:Tag)
                WHERE t.category = 'performance'
                RETURN count(t) as performance_tag_count
            """)

            count_record = count_result.single()
            if count_record:
                print(f"\n📊 Total performance tags in system: {count_record['performance_tag_count']}")

            # Show all performance tags for confirmation
            print(f"\n🏷️  All performance tags:")
            list_result = session.run("""
                MATCH (t:Tag)
                WHERE t.category = 'performance'
                RETURN t.name as name, t.description as description
                ORDER BY t.name
            """)

            for record in list_result:
                print(f"   • {record['name']}: {record['description']}")

    except Exception as e:
        logger.error(f"Error creating performance tags: {e}")
        print(f"❌ Error creating performance tags: {e}")
        return False

    finally:
        if driver:
            driver.close()

    return True

if __name__ == "__main__":
    print("🚀 Creating performance tags for Cortex system...")
    print("=" * 60)

    success = create_performance_tags()

    if success:
        print("=" * 60)
        print("✅ Performance tags creation completed successfully!")
        print("\nYou can now use these tags:")
        print("   • performance-metrics: For performance measurement notes")
        print("   • system-optimization: For system improvement notes")
        print("   • command-tracking: For command monitoring notes")
        print("\nTo assign these tags to notes, use the governance CLI or Neo4j directly.")
    else:
        print("❌ Performance tags creation failed. Check logs for details.")
        sys.exit(1)
