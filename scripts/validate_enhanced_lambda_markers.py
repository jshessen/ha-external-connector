#!/usr/bin/env python3
"""
Enhanced Lambda Deployment Marker Validation Script

This script provides comprehensive validation of Lambda function deployment markers
with performance metrics, detailed reporting, and infrastructure synchronization
validation.

Features:
- Comprehensive marker validation with performance metrics
- Orphaned code detection
- Infrastructure sync validation
- Enhanced error reporting
- Performance benchmarking
- Documentation generation

Usage:
    python scripts/validate_enhanced_lambda_markers.py
    python scripts/validate_enhanced_lambda_markers.py --verbose
    python scripts/validate_enhanced_lambda_markers.py --benchmark
"""

import argparse
import time
from pathlib import Path

from lambda_deployment.deployment_manager import LambdaMarkerValidator


def generate_validation_report(results: dict, verbose: bool = False) -> str:
    """Generate comprehensive validation report"""
    report_lines = [
        "🔍 Enhanced Lambda Deployment Marker Validation Report",
        "=" * 60,
        ""
    ]
    
    total_files = len(results)
    valid_files = sum(1 for result in results.values() if result.is_valid)
    
    # Summary section
    report_lines.extend([
        f"📊 Summary:",
        f"   Total files validated: {total_files}",
        f"   Valid files: {valid_files}",
        f"   Files with issues: {total_files - valid_files}",
        f"   Success rate: {(valid_files/total_files)*100:.1f}%",
        ""
    ])
    
    # Detailed file results
    for file_name, result in results.items():
        report_lines.append(f"📁 {file_name}")
        
        if result.is_valid:
            report_lines.append("   ✅ All validations passed")
        else:
            report_lines.append("   ❌ Validation failed:")
            
            if result.missing_markers:
                report_lines.append("      Missing markers:")
                for marker in result.missing_markers:
                    report_lines.append(f"         • {marker}")
                    
            if result.orphaned_code:
                report_lines.append("      Orphaned code:")
                for code in result.orphaned_code:
                    report_lines.append(f"         • {code}")
                    
            if result.marker_issues:
                report_lines.append("      Marker format issues:")
                for issue in result.marker_issues:
                    report_lines.append(f"         • {issue}")
        
        # Performance metrics
        if verbose and result.performance_metrics:
            metrics = result.performance_metrics
            if "validation_time" in metrics:
                report_lines.append(f"   ⚡ Validation time: {metrics['validation_time']:.4f}s")
        
        report_lines.append("")
    
    # Performance summary
    if verbose:
        total_time = sum(
            result.performance_metrics.get("validation_time", 0)
            for result in results.values()
        )
        avg_time = total_time / total_files if total_files > 0 else 0
        
        report_lines.extend([
            "🎯 Performance Metrics:",
            f"   Total validation time: {total_time:.4f}s",
            f"   Average per file: {avg_time:.4f}s", 
            ""
        ])
    
    return "\n".join(report_lines)


def validate_infrastructure_sync() -> dict:
    """Validate infrastructure deployment synchronization"""
    workspace_root = Path.cwd()
    source_dir = workspace_root / "src/ha_connector/integrations/alexa/lambda_functions"
    infra_dir = workspace_root / "infrastructure/deployment"
    
    sync_results = {
        "infrastructure_exists": infra_dir.exists(),
        "source_files": [],
        "deployment_files": [],
        "missing_deployments": [],
        "orphaned_deployments": []
    }
    
    # Check source files
    if source_dir.exists():
        lambda_files = ["oauth_gateway.py", "smart_home_bridge.py"]
        for file_name in lambda_files:
            source_file = source_dir / file_name
            if source_file.exists():
                sync_results["source_files"].append(file_name)
    
    # Check deployment files
    if infra_dir.exists():
        for file_path in infra_dir.glob("*.py"):
            sync_results["deployment_files"].append(file_path.name)
    
    # Find mismatches
    for source_file in sync_results["source_files"]:
        if source_file not in sync_results["deployment_files"]:
            sync_results["missing_deployments"].append(source_file)
    
    for deploy_file in sync_results["deployment_files"]:
        if deploy_file not in sync_results["source_files"]:
            sync_results["orphaned_deployments"].append(deploy_file)
    
    return sync_results


def run_performance_benchmark() -> dict:
    """Run performance benchmark tests"""
    workspace_root = Path.cwd()
    lambda_dir = workspace_root / "src/ha_connector/integrations/alexa/lambda_functions"
    
    if not lambda_dir.exists():
        return {"error": "Lambda functions directory not found"}
    
    validator = LambdaMarkerValidator(str(lambda_dir))
    
    # Benchmark individual file validation
    benchmark_results = {}
    
    lambda_files = [
        "oauth_gateway.py",
        "smart_home_bridge.py", 
        "configuration_manager.py",
        "shared_configuration.py"
    ]
    
    for file_name in lambda_files:
        file_path = lambda_dir / file_name
        if not file_path.exists():
            continue
            
        # Run multiple iterations for better accuracy
        iterations = 5
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            validator.validate_lambda_markers(file_path)
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        benchmark_results[file_name] = {
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "iterations": iterations
        }
    
    return benchmark_results


def main():
    """Main validation function with enhanced features"""
    parser = argparse.ArgumentParser(
        description="Enhanced Lambda deployment marker validation"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose output with performance metrics"
    )
    parser.add_argument(
        "--benchmark", "-b",
        action="store_true", 
        help="Run performance benchmarks"
    )
    parser.add_argument(
        "--infrastructure", "-i",
        action="store_true",
        help="Validate infrastructure synchronization"
    )
    
    args = parser.parse_args()
    
    print("🔍 Enhanced Lambda Deployment Marker Validation\n")
    
    # Core marker validation
    workspace_root = Path.cwd()
    lambda_dir = workspace_root / "src/ha_connector/integrations/alexa/lambda_functions"
    
    if not lambda_dir.exists():
        print(f"❌ Lambda functions directory not found: {lambda_dir}")
        return False
    
    validator = LambdaMarkerValidator(str(lambda_dir))
    
    start_time = time.time()
    results = validator.validate_all_lambda_markers()
    total_time = time.time() - start_time
    
    # Generate and display report
    report = generate_validation_report(results, args.verbose)
    print(report)
    
    # Infrastructure sync validation
    if args.infrastructure:
        print("🏗️  Infrastructure Synchronization Validation")
        print("-" * 50)
        
        sync_results = validate_infrastructure_sync()
        
        print(f"Infrastructure directory exists: {sync_results['infrastructure_exists']}")
        print(f"Source files: {len(sync_results['source_files'])}")
        print(f"Deployment files: {len(sync_results['deployment_files'])}")
        
        if sync_results["missing_deployments"]:
            print("⚠️  Missing deployment files:")
            for file_name in sync_results["missing_deployments"]:
                print(f"   • {file_name}")
        
        if sync_results["orphaned_deployments"]:
            print("⚠️  Orphaned deployment files:")
            for file_name in sync_results["orphaned_deployments"]:
                print(f"   • {file_name}")
        
        if not sync_results["missing_deployments"] and not sync_results["orphaned_deployments"]:
            print("✅ Infrastructure is synchronized")
        
        print()
    
    # Performance benchmarks
    if args.benchmark:
        print("⚡ Performance Benchmarks")
        print("-" * 30)
        
        benchmark_results = run_performance_benchmark()
        
        if "error" in benchmark_results:
            print(f"❌ Benchmark error: {benchmark_results['error']}")
        else:
            for file_name, metrics in benchmark_results.items():
                print(f"📁 {file_name}:")
                print(f"   Average: {metrics['average_time']:.4f}s")
                print(f"   Range: {metrics['min_time']:.4f}s - {metrics['max_time']:.4f}s")
                print(f"   Iterations: {metrics['iterations']}")
                print()
        
        print()
    
    # Overall summary
    valid_count = sum(1 for result in results.values() if result.is_valid)
    total_count = len(results)
    
    print(f"🎯 Overall Results:")
    print(f"   Validation completed in {total_time:.4f}s")
    print(f"   Files processed: {total_count}")
    print(f"   Success rate: {(valid_count/total_count)*100:.1f}%")
    
    if valid_count == total_count:
        print("\n🚀 All Lambda functions have valid deployment markers!")
        print("   System is ready for automated deployment.")
        return True
    else:
        print(f"\n❌ {total_count - valid_count} files have marker issues.")
        print("   Please fix issues before proceeding with deployment.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)