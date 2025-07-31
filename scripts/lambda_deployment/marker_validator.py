#!/usr/bin/env python3
"""
Standalone Lambda Marker Validator

Command-line tool for validating Lambda deployment markers across files and directories.
Provides comprehensive validation reporting with performance metrics and detailed analysis.

Features:
- Recursive directory validation
- Performance benchmarking
- Infrastructure synchronization checks
- Detailed validation reports
- Export capabilities (JSON, HTML)
- Integration with deployment system
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from .marker_system import DeploymentMarkerSystem
from .validation_system import DeploymentValidationSystem, ValidationType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for beautiful output
console = Console()


class LambdaMarkerValidator:
    """
    Standalone Lambda marker validation tool
    
    Provides comprehensive validation of Lambda deployment markers
    with detailed reporting and performance analysis.
    """

    def __init__(self, source_dir: str):
        """Initialize validator with source directory"""
        self.source_dir = Path(source_dir)
        self.marker_system = DeploymentMarkerSystem()
        self.validation_system = DeploymentValidationSystem()
        self.results = {}

    def validate_all_lambda_markers(self, verbose: bool = False) -> dict[str, Any]:
        """
        Validate all Lambda functions in source directory
        
        Args:
            verbose: Enable verbose output
            
        Returns:
            Comprehensive validation results
        """
        start_time = time.time()

        # Find all Python files
        python_files = list(self.source_dir.rglob("*.py"))
        lambda_files = [f for f in python_files if self._is_lambda_file(f)]

        console.print("\n🔍 [bold blue]Lambda Deployment Marker Validation[/bold blue]")
        console.print(f"📁 Source directory: [cyan]{self.source_dir}[/cyan]")
        console.print(f"📄 Found {len(lambda_files)} Lambda function files")

        validation_results = {}
        total_issues = 0
        valid_files = 0

        with Progress() as progress:
            task = progress.add_task("Validating files...", total=len(lambda_files))

            for lambda_file in lambda_files:
                # Validate markers for this file
                file_result = self._validate_file_markers(lambda_file, verbose)
                validation_results[lambda_file.name] = file_result

                if file_result['is_valid']:
                    valid_files += 1

                total_issues += file_result.get('error_count', 0)

                progress.advance(task)

                if verbose:
                    self._print_file_result(lambda_file, file_result)

        # Calculate summary statistics
        elapsed_time = time.time() - start_time
        success_rate = (valid_files / len(lambda_files)) * 100 if lambda_files else 0

        summary = {
            'total_files': len(lambda_files),
            'valid_files': valid_files,
            'files_with_issues': len(lambda_files) - valid_files,
            'total_issues': total_issues,
            'success_rate': success_rate,
            'validation_time': elapsed_time,
            'files': validation_results
        }

        self._print_summary(summary)

        return summary

    def _validate_file_markers(self, file_path: Path, verbose: bool = False) -> dict[str, Any]:
        """Validate markers in a specific file"""
        try:
            # Use marker system for validation
            marker_validation = self.marker_system.validate_all_markers(file_path)

            # Enhance with additional validation
            validation_result = self.validation_system.validate_file(
                file_path,
                [ValidationType.MARKERS, ValidationType.SYNTAX]
            )

            return {
                'is_valid': marker_validation['is_valid'] and validation_result.is_valid,
                'total_blocks': marker_validation.get('total_blocks', 0),
                'valid_blocks': marker_validation.get('valid_blocks', 0),
                'error_count': marker_validation.get('error_count', 0),
                'warning_count': marker_validation.get('warning_count', 0),
                'orphaned_lines': len(marker_validation.get('orphaned_lines', [])),
                'blocks': marker_validation.get('blocks', []),
                'validation_time': validation_result.validation_time,
                'summary': marker_validation.get('summary', ''),
                'issues': validation_result.issues
            }

        except Exception as e:
            logger.error("Failed to validate %s: %s", file_path, str(e))
            return {
                'is_valid': False,
                'error_count': 1,
                'error_message': str(e),
                'validation_time': 0.0
            }

    def _is_lambda_file(self, file_path: Path) -> bool:
        """Check if file is a Lambda function file"""
        # Skip test files and __init__.py files
        if (file_path.name.startswith('test_') or
            file_path.name == '__init__.py' or
            'test' in str(file_path).lower()):
            return False

        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for Lambda function indicators
            lambda_indicators = [
                'lambda_handler',
                'def handler(',
                'aws_lambda',
                'boto3',
                'IMPORT_BLOCK_START',
                'FUNCTION_BLOCK_START'
            ]

            return any(indicator in content for indicator in lambda_indicators)

        except Exception:
            return False

    def _print_file_result(self, file_path: Path, result: dict[str, Any]) -> None:
        """Print detailed file validation result"""
        status = "✅" if result['is_valid'] else "❌"

        console.print(f"\n{status} [bold]{file_path.name}[/bold]")

        if result['is_valid']:
            console.print("   [green]All validations passed[/green]")
        else:
            console.print(f"   [red]{result.get('error_count', 0)} errors, "
                         f"{result.get('warning_count', 0)} warnings[/red]")

        console.print(f"   ⚡ Validation time: {result.get('validation_time', 0):.4f}s")

        # Show block details
        if 'total_blocks' in result:
            console.print(f"   📦 Blocks: {result['valid_blocks']}/{result['total_blocks']} valid")

        # Show orphaned code
        if result.get('orphaned_lines', 0) > 0:
            console.print(f"   ⚠️  {result['orphaned_lines']} orphaned lines detected")

    def _print_summary(self, summary: dict[str, Any]) -> None:
        """Print comprehensive validation summary"""
        console.print("\n" + "=" * 60)

        # Summary panel
        summary_text = f"""
📊 [bold]Validation Summary[/bold]
   Total files validated: [cyan]{summary['total_files']}[/cyan]
   Valid files: [green]{summary['valid_files']}[/green]
   Files with issues: [red]{summary['files_with_issues']}[/red]
   Success rate: [{'green' if summary['success_rate'] >= 90 else 'yellow' if summary['success_rate'] >= 70 else 'red'}]{summary['success_rate']:.1f}%[/]
   Total issues: [red]{summary['total_issues']}[/red]

🎯 [bold]Performance Metrics[/bold]
   Total validation time: [cyan]{summary['validation_time']:.4f}s[/cyan]
   Average per file: [cyan]{summary['validation_time'] / max(summary['total_files'], 1):.4f}s[/cyan]
        """

        console.print(Panel(summary_text.strip(), title="🔍 Enhanced Lambda Deployment Marker Validation Report"))

        # File details table
        if summary['files']:
            table = Table(title="📁 File Validation Details")
            table.add_column("File", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Blocks", justify="center")
            table.add_column("Issues", justify="center")
            table.add_column("Time (s)", justify="right")

            for file_name, result in summary['files'].items():
                status = "✅ Valid" if result['is_valid'] else "❌ Invalid"
                blocks = f"{result.get('valid_blocks', 0)}/{result.get('total_blocks', 0)}"
                issues = str(result.get('error_count', 0))
                time_str = f"{result.get('validation_time', 0):.4f}"

                table.add_row(file_name, status, blocks, issues, time_str)

            console.print(table)

        # Final status
        if summary['success_rate'] == 100.0:
            console.print("\n🚀 [bold green]All Lambda functions have valid deployment markers![/bold green]")
            console.print("   [green]System is ready for automated deployment.[/green]")
        else:
            console.print(f"\n⚠️  [bold yellow]{summary['files_with_issues']} files need attention[/bold yellow]")
            console.print("   [yellow]Review and fix marker issues before deployment.[/yellow]")

    def validate_infrastructure_sync(self, infrastructure_dir: str) -> dict[str, Any]:
        """
        Validate synchronization with infrastructure deployment files
        
        Args:
            infrastructure_dir: Path to infrastructure deployment directory
            
        Returns:
            Synchronization validation results
        """
        infra_path = Path(infrastructure_dir)

        console.print("\n🔄 [bold blue]Infrastructure Synchronization Check[/bold blue]")
        console.print(f"📁 Infrastructure directory: [cyan]{infra_path}[/cyan]")

        if not infra_path.exists():
            console.print("❌ [red]Infrastructure directory not found[/red]")
            return {'is_synchronized': False, 'error': 'Directory not found'}

        # Find Lambda function directories
        lambda_dirs = [d for d in infra_path.iterdir() if d.is_dir()]

        sync_results = {}

        for lambda_dir in lambda_dirs:
            lambda_function_file = lambda_dir / "lambda_function.py"

            if lambda_function_file.exists():
                # Find corresponding source file
                source_file = self._find_source_file(lambda_dir.name)

                if source_file:
                    sync_result = self._compare_marker_blocks(source_file, lambda_function_file)
                    sync_results[lambda_dir.name] = sync_result
                else:
                    sync_results[lambda_dir.name] = {
                        'is_synchronized': False,
                        'error': 'Source file not found'
                    }

        self._print_sync_results(sync_results)

        return {
            'is_synchronized': all(r.get('is_synchronized', False) for r in sync_results.values()),
            'functions': sync_results
        }

    def _find_source_file(self, function_name: str) -> Path | None:
        """Find source file for Lambda function"""
        # Try common naming patterns
        potential_names = [
            f"{function_name}.py",
            f"{function_name}_handler.py",
            f"{function_name}_function.py"
        ]

        for name in potential_names:
            for file_path in self.source_dir.rglob(name):
                if self._is_lambda_file(file_path):
                    return file_path

        return None

    def _compare_marker_blocks(self, source_file: Path, infra_file: Path) -> dict[str, Any]:
        """Compare marker blocks between source and infrastructure files"""
        try:
            source_blocks = self.marker_system.extract_marker_blocks(source_file)
            infra_blocks = self.marker_system.extract_marker_blocks(infra_file)

            # Compare block counts and content
            is_synchronized = (
                len(source_blocks) == len(infra_blocks) and
                all(self._blocks_match(sb, ib) for sb, ib in zip(source_blocks, infra_blocks, strict=False))
            )

            return {
                'is_synchronized': is_synchronized,
                'source_blocks': len(source_blocks),
                'infra_blocks': len(infra_blocks),
                'source_file': str(source_file),
                'infra_file': str(infra_file)
            }

        except Exception as e:
            return {
                'is_synchronized': False,
                'error': str(e)
            }

    def _blocks_match(self, source_block, infra_block) -> bool:
        """Check if two marker blocks match"""
        return (
            source_block.start_marker == infra_block.start_marker and
            source_block.end_marker == infra_block.end_marker and
            len(source_block.content) == len(infra_block.content)
        )

    def _print_sync_results(self, sync_results: dict[str, Any]) -> None:
        """Print infrastructure synchronization results"""
        if not sync_results:
            console.print("❌ [red]No Lambda functions found in infrastructure directory[/red]")
            return

        table = Table(title="🔄 Infrastructure Synchronization Status")
        table.add_column("Function", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Source Blocks", justify="center")
        table.add_column("Infra Blocks", justify="center")

        for function_name, result in sync_results.items():
            if result.get('is_synchronized', False):
                status = "✅ Synced"
            else:
                status = f"❌ {result.get('error', 'Out of sync')}"

            source_blocks = str(result.get('source_blocks', '?'))
            infra_blocks = str(result.get('infra_blocks', '?'))

            table.add_row(function_name, status, source_blocks, infra_blocks)

        console.print(table)

    def export_results(self, results: dict[str, Any], output_file: str, format_type: str = "json") -> None:
        """Export validation results to file"""
        output_path = Path(output_file)

        try:
            if format_type.lower() == "json":
                with output_path.open('w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            console.print(f"📄 [green]Results exported to {output_path}[/green]")

        except Exception as e:
            console.print(f"❌ [red]Failed to export results: {str(e)}[/red]")

    def benchmark_performance(self, iterations: int = 5) -> dict[str, Any]:
        """Benchmark validation performance"""
        console.print(f"\n⚡ [bold blue]Performance Benchmark ({iterations} iterations)[/bold blue]")

        python_files = list(self.source_dir.rglob("*.py"))
        lambda_files = [f for f in python_files if self._is_lambda_file(f)]

        if not lambda_files:
            console.print("❌ [red]No Lambda files found for benchmarking[/red]")
            return {'error': 'No files found'}

        times = []

        with Progress() as progress:
            task = progress.add_task("Running benchmark...", total=iterations)

            for i in range(iterations):
                start_time = time.time()

                for lambda_file in lambda_files:
                    self._validate_file_markers(lambda_file, verbose=False)

                elapsed = time.time() - start_time
                times.append(elapsed)

                progress.advance(task)

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        files_per_second = len(lambda_files) / avg_time

        benchmark_results = {
            'iterations': iterations,
            'total_files': len(lambda_files),
            'average_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'files_per_second': files_per_second,
            'times': times
        }

        # Print benchmark results
        console.print("\n📊 [bold]Benchmark Results[/bold]")
        console.print(f"   Average time: [cyan]{avg_time:.4f}s[/cyan]")
        console.print(f"   Min time: [green]{min_time:.4f}s[/green]")
        console.print(f"   Max time: [red]{max_time:.4f}s[/red]")
        console.print(f"   Files per second: [yellow]{files_per_second:.1f}[/yellow]")

        return benchmark_results


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Lambda Deployment Marker Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s src/lambda_functions --verbose
  %(prog)s src/lambda_functions --infrastructure infrastructure/deployment
  %(prog)s src/lambda_functions --benchmark --iterations 10
  %(prog)s src/lambda_functions --export results.json
        """
    )

    parser.add_argument(
        "source_dir",
        help="Source directory containing Lambda functions"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--infrastructure", "-i",
        help="Infrastructure deployment directory for sync check"
    )

    parser.add_argument(
        "--benchmark", "-b",
        action="store_true",
        help="Run performance benchmark"
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of benchmark iterations (default: 5)"
    )

    parser.add_argument(
        "--export", "-e",
        help="Export results to file (JSON format)"
    )

    parser.add_argument(
        "--log-level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Set logging level"
    )

    args = parser.parse_args()

    # Configure logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Validate source directory
    source_path = Path(args.source_dir)
    if not source_path.exists():
        console.print(f"❌ [red]Source directory not found: {source_path}[/red]")
        sys.exit(1)

    # Create validator
    validator = LambdaMarkerValidator(str(source_path))

    try:
        # Run main validation
        results = validator.validate_all_lambda_markers(verbose=args.verbose)

        # Run infrastructure sync check if requested
        if args.infrastructure:
            sync_results = validator.validate_infrastructure_sync(args.infrastructure)
            results['infrastructure_sync'] = sync_results

        # Run benchmark if requested
        if args.benchmark:
            benchmark_results = validator.benchmark_performance(args.iterations)
            results['benchmark'] = benchmark_results

        # Export results if requested
        if args.export:
            validator.export_results(results, args.export)

        # Exit with appropriate code
        if results.get('success_rate', 0) == 100.0:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n❌ [red]Validation interrupted by user[/red]")
        sys.exit(130)
    except Exception as e:
        console.print(f"❌ [red]Validation failed: {str(e)}[/red]")
        logger.exception("Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
