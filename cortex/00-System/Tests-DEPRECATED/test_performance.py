#!/usr/bin/env python3
"""
Performance Tests for Cortex System
Tests system performance, memory usage, and scalability
"""

import pytest
import time
import psutil
import tempfile
import shutil
from pathlib import Path
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Add system paths
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Management-Service')

from multi_vault_ai import MultiVaultAILearningEngine
from cross_vault_linker import CrossVaultLinker
from cortex_management import CortexManagementService

class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        
    def start(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        
    def update_peak_memory(self):
        """Update peak memory usage"""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
            
    def stop(self):
        """Stop performance monitoring"""
        self.end_time = time.time()
        self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
    @property
    def duration(self):
        """Get test duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
        
    @property
    def memory_delta(self):
        """Get memory usage change in MB"""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return None
        
    def report(self):
        """Generate performance report"""
        return {
            'duration_seconds': self.duration,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': self.end_memory,
            'peak_memory_mb': self.peak_memory,
            'memory_delta_mb': self.memory_delta
        }

class TestDataGenerator:
    """Generate test data for performance testing"""
    
    @staticmethod
    def create_large_vault(vault_path: Path, file_count: int = 100, tags_per_file: int = 10):
        """Create a vault with many files for performance testing"""
        vault_path.mkdir(parents=True, exist_ok=True)
        
        # Create .obsidian directory
        obsidian_dir = vault_path / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)
        obsidian_dir.joinpath("app.json").write_text('{"vaultId":"perf-test"}')
        
        # Create directories
        for i in range(10):
            (vault_path / f"category-{i:02d}").mkdir(exist_ok=True)
        
        # Generate tag pool
        tag_pool = [f"tag-{i:03d}" for i in range(50)]
        
        # Create many files
        for i in range(file_count):
            category = i % 10
            file_path = vault_path / f"category-{category:02d}" / f"file-{i:04d}.md"
            
            # Select random tags
            import random
            selected_tags = random.sample(tag_pool, min(tags_per_file, len(tag_pool)))
            tag_string = ' '.join([f'#{tag}' for tag in selected_tags])
            
            content = f"""# File {i:04d}

## Content
This is file number {i} for performance testing.

## Tags
{tag_string}

## Additional Content
{' '.join(['Content'] * 50)}  # Make file larger
"""
            file_path.write_text(content, encoding='utf-8')
        
        return vault_path

class TestPerformanceAIEngine:
    """Performance tests for AI Learning Engine"""
    
    @pytest.fixture
    def large_vault(self):
        """Create large vault for performance testing"""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "large-vault"
        TestDataGenerator.create_large_vault(vault_path, file_count=200, tags_per_file=15)
        yield vault_path
        shutil.rmtree(temp_dir)
    
    def test_large_vault_analysis_performance(self, large_vault):
        """Test AI engine performance with large vault"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        # Initialize AI engine
        ai_engine = MultiVaultAILearningEngine(str(large_vault))
        monitor.update_peak_memory()
        
        # Run analysis
        report = ai_engine.run_full_analysis()
        monitor.update_peak_memory()
        
        monitor.stop()
        perf_report = monitor.report()
        
        # Performance assertions
        assert perf_report['duration_seconds'] < 30  # Should complete within 30 seconds
        assert perf_report['peak_memory_mb'] < 500   # Should use less than 500MB
        assert report is not None
        
        print(f"Large vault analysis performance: {perf_report}")
    
    def test_concurrent_operations(self, large_vault):
        """Test system performance under concurrent operations"""
        hub_path = large_vault
        
        management = CortexManagementService(str(hub_path))
        
        def run_cycle():
            """Run a management cycle"""
            return management.run_full_cycle()
        
        # Test concurrent execution (simulating multiple requests)
        monitor = PerformanceMonitor()
        monitor.start()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_cycle) for _ in range(3)]
            results = [future.result() for future in futures]
        
        monitor.stop()
        perf_report = monitor.report()
        
        # All operations should succeed
        assert all(results)
        assert perf_report['duration_seconds'] < 300  # Should complete within 5 minutes
        
        print(f"Concurrent operations performance: {perf_report}")

class TestStressTests:
    """Stress tests for system limits"""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        temp_dir = tempfile.mkdtemp()
        hub_path = Path(temp_dir) / "cortex"
        TestDataGenerator.create_large_vault(hub_path, file_count=50)
        
        try:
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Run multiple cycles
            for i in range(10):
                management = CortexManagementService(str(hub_path))
                management.run_full_cycle()
                
                # Force garbage collection
                import gc
                gc.collect()
                
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable
                assert memory_growth < 200, f"Excessive memory growth: {memory_growth}MB"
            
            print(f"Memory leak test passed. Final growth: {memory_growth}MB")
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_large_file_handling(self):
        """Test system with very large files"""
        temp_dir = tempfile.mkdtemp()
        vault_path = Path(temp_dir) / "large-files"
        vault_path.mkdir(parents=True)
        
        # Create .obsidian directory
        obsidian_dir = vault_path / ".obsidian"
        obsidian_dir.mkdir()
        obsidian_dir.joinpath("app.json").write_text('{"vaultId":"large-files"}')
        
        try:
            # Create a very large file (10MB)
            large_content = "# Large File\n\n" + ("Large content line with #tags and #more-tags\n" * 100000)
            large_file = vault_path / "large-file.md"
            large_file.write_text(large_content, encoding='utf-8')
            
            monitor = PerformanceMonitor()
            monitor.start()
            
            ai_engine = MultiVaultAILearningEngine(str(vault_path))
            report = ai_engine.run_full_analysis()
            
            monitor.stop()
            perf_report = monitor.report()
            
            # Should handle large files gracefully
            assert report is not None
            assert perf_report['duration_seconds'] < 60
            
            print(f"Large file handling test: {perf_report}")
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_maximum_vault_count(self):
        """Test system with maximum number of vaults"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create hub vault
            hub_path = Path(temp_dir) / "cortex"
            TestDataGenerator.create_large_vault(hub_path, file_count=20)
            
            # Create many project vaults
            vault_count = 20
            for i in range(vault_count):
                project_path = Path(temp_dir) / f"project-{i:03d}"
                TestDataGenerator.create_large_vault(project_path, file_count=30, tags_per_file=8)
            
            monitor = PerformanceMonitor()
            monitor.start()
            
            management = CortexManagementService(str(hub_path))
            success = management.run_full_cycle()
            
            monitor.stop()
            perf_report = monitor.report()
            
            # Should handle many vaults
            assert success is True
            assert perf_report['duration_seconds'] < 600  # 10 minutes max
            assert management.service_stats['vaults_discovered'] >= vault_count
            
            print(f"Maximum vault count test ({vault_count} vaults): {perf_report}")
            
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])
