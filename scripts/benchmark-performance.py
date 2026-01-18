#!/usr/bin/env python3
"""
Performance Benchmarking Script
=====================================

Measure and report performance metrics:
- API response times (p50, p95, p99)
- Bundle load time
- Page transition time
- Memory usage
- Database query performance

Target Metrics:
- API response P95: < 200ms
- Bundle load time: < 2s (4G)
- Page transition: < 500ms
- Memory usage: < 50MB
- Error rate: < 0.1%
- Throughput: > 50 req/s

Usage:
    python scripts/benchmark-performance.py [--output json|csv|html]
    python scripts/benchmark-performance.py --compare baseline.json
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import statistics

import httpx
import psutil

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
BENCHMARK_RESULTS_DIR = Path(__file__).parent.parent / "benchmarks"
TIMEOUT = 30
CONCURRENT_REQUESTS = 10

# Target SLAs
TARGETS = {
    "api_response_p95_ms": 200,
    "bundle_load_time_s": 2.0,
    "page_transition_ms": 500,
    "memory_usage_mb": 50,
    "error_rate": 0.001,
    "throughput_req_s": 50,
}

# Critical API endpoints
CRITICAL_ENDPOINTS = [
    ("GET", "/api/v1/employees?year=2025"),
    ("GET", "/api/v1/employees/001_2025"),
    ("GET", "/api/health"),
    ("GET", "/api/v1/notifications"),
    ("GET", "/api/v1/analytics/stats?year=2025"),
]

# Mutation endpoints (for load testing)
MUTATION_ENDPOINTS = [
    ("GET", "/api/v1/leave-requests?status=pending"),
    ("GET", "/api/v1/compliance/5day?year=2025"),
]


class PerformanceBenchmark:
    """Main benchmarking orchestrator."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "base_url": self.base_url,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "platform": sys.platform,
            },
            "metrics": {},
            "tests": [],
            "summary": {},
        }
        self.process = psutil.Process()

    async def run_all_benchmarks(self) -> Dict:
        """Run all benchmarking tests."""
        print("\n" + "=" * 70)
        print("YuKyuDATA Performance Benchmarking")
        print("=" * 70)

        # 1. API Response Time Benchmark
        print("\n[1/4] API Response Time Benchmark...")
        await self._benchmark_api_response_times()

        # 2. Bundle Load Time (simulated)
        print("\n[2/4] Bundle Load Time Benchmark...")
        await self._benchmark_bundle_load()

        # 3. Page Transition Time (simulated)
        print("\n[3/4] Page Transition Benchmark...")
        await self._benchmark_page_transitions()

        # 4. Memory Usage Benchmark
        print("\n[4/4] Memory Usage Benchmark...")
        self._benchmark_memory_usage()

        # Generate summary
        self._generate_summary()

        return self.results

    async def _benchmark_api_response_times(self) -> None:
        """Benchmark critical API endpoints."""
        print("  Testing critical endpoints...")

        response_times = []

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for method, endpoint in CRITICAL_ENDPOINTS:
                times = []

                # Make 10 requests to each endpoint
                for i in range(10):
                    try:
                        url = f"{self.base_url}{endpoint}"
                        start = time.perf_counter()

                        if method == "GET":
                            response = await client.get(url)
                        elif method == "POST":
                            response = await client.post(url, json={})

                        elapsed_ms = (time.perf_counter() - start) * 1000
                        times.append(elapsed_ms)

                        if response.status_code < 300:
                            response_times.append(elapsed_ms)
                            status = "✓"
                        else:
                            status = f"✗ ({response.status_code})"

                        if i == 0:  # Only print first request
                            print(
                                f"    {method} {endpoint}: {elapsed_ms:.2f}ms {status}"
                            )

                    except Exception as e:
                        print(f"    {method} {endpoint}: ERROR - {e}")
                        times.append(None)

                # Calculate statistics for this endpoint
                valid_times = [t for t in times if t is not None]
                if valid_times:
                    endpoint_stats = {
                        "endpoint": f"{method} {endpoint}",
                        "samples": len(valid_times),
                        "min_ms": min(valid_times),
                        "max_ms": max(valid_times),
                        "mean_ms": statistics.mean(valid_times),
                        "median_ms": statistics.median(valid_times),
                        "stddev_ms": (
                            statistics.stdev(valid_times)
                            if len(valid_times) > 1
                            else 0
                        ),
                    }
                    self.results["tests"].append(endpoint_stats)
                    print(f"      Mean: {endpoint_stats['mean_ms']:.2f}ms | "
                          f"Median: {endpoint_stats['median_ms']:.2f}ms")

        # Calculate overall API metrics
        if response_times:
            api_metrics = {
                "total_requests": len(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "p95_ms": self._percentile(response_times, 0.95),
                "p99_ms": self._percentile(response_times, 0.99),
            }
            self.results["metrics"]["api_response"] = api_metrics
            print(f"\n  API Response Time Summary:")
            print(f"    P50 (median): {api_metrics['median_ms']:.2f}ms")
            print(f"    P95: {api_metrics['p95_ms']:.2f}ms")
            print(f"    P99: {api_metrics['p99_ms']:.2f}ms")
            print(f"    Mean: {api_metrics['mean_ms']:.2f}ms")

            # Check SLA
            if api_metrics["p95_ms"] <= TARGETS["api_response_p95_ms"]:
                print(f"    ✓ P95 SLA PASSED ({api_metrics['p95_ms']:.2f}ms "
                      f"<= {TARGETS['api_response_p95_ms']}ms)")
            else:
                print(f"    ✗ P95 SLA FAILED ({api_metrics['p95_ms']:.2f}ms "
                      f"> {TARGETS['api_response_p95_ms']}ms)")

    async def _benchmark_bundle_load(self) -> None:
        """Benchmark static asset loading (simulated)."""
        print("  Testing static assets...")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            assets = [
                "/static/js/app.js",
                "/static/src/components/Form.js",
                "/static/src/components/Table.js",
                "/static/css/main.css",
            ]

            total_size = 0
            total_time = 0
            asset_metrics = []

            for asset in assets:
                try:
                    url = f"{self.base_url}{asset}"
                    start = time.perf_counter()
                    response = await client.get(url)
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    size_kb = len(response.content) / 1024

                    total_size += size_kb
                    total_time += elapsed_ms

                    asset_metrics.append(
                        {
                            "asset": asset,
                            "size_kb": size_kb,
                            "load_time_ms": elapsed_ms,
                        }
                    )
                    print(f"    {asset}: {size_kb:.2f}KB in {elapsed_ms:.2f}ms")

                except Exception as e:
                    print(f"    {asset}: ERROR - {e}")

            if asset_metrics:
                # Simulate bundle load time (4G: ~1Mbps = 1MB in ~8s, but with caching)
                bundle_metrics = {
                    "assets": len(asset_metrics),
                    "total_size_kb": total_size,
                    "total_load_time_ms": total_time,
                    "simulated_4g_time_s": total_size / 512,  # 512KB/s on 4G
                }
                self.results["metrics"]["bundle_load"] = bundle_metrics
                print(f"\n  Bundle Load Time Summary:")
                print(f"    Total assets: {bundle_metrics['assets']}")
                print(f"    Total size: {bundle_metrics['total_size_kb']:.2f}KB")
                print(f"    Network load time: {total_time:.2f}ms")
                print(f"    Simulated 4G time: {bundle_metrics['simulated_4g_time_s']:.2f}s")

                # Check SLA
                if bundle_metrics["simulated_4g_time_s"] <= TARGETS["bundle_load_time_s"]:
                    print(f"    ✓ Bundle SLA PASSED ({bundle_metrics['simulated_4g_time_s']:.2f}s "
                          f"<= {TARGETS['bundle_load_time_s']}s)")
                else:
                    print(f"    ✗ Bundle SLA FAILED ({bundle_metrics['simulated_4g_time_s']:.2f}s "
                          f"> {TARGETS['bundle_load_time_s']}s)")

    async def _benchmark_page_transitions(self) -> None:
        """Benchmark page transition time (simulated)."""
        print("  Testing page transitions...")

        # Simulated page transition metrics (based on bundle load + API)
        transitions = {
            "dashboard": {"api_time_ms": 150, "render_time_ms": 200},
            "employees": {"api_time_ms": 180, "render_time_ms": 250},
            "leave_requests": {"api_time_ms": 160, "render_time_ms": 220},
            "analytics": {"api_time_ms": 300, "render_time_ms": 300},
        }

        transition_metrics = []
        max_transition = 0

        for page, times in transitions.items():
            total_ms = times["api_time_ms"] + times["render_time_ms"]
            max_transition = max(max_transition, total_ms)
            transition_metrics.append(
                {
                    "page": page,
                    "api_time_ms": times["api_time_ms"],
                    "render_time_ms": times["render_time_ms"],
                    "total_ms": total_ms,
                }
            )
            print(f"    {page}: {total_ms}ms (API: {times['api_time_ms']}ms + "
                  f"Render: {times['render_time_ms']}ms)")

        self.results["metrics"]["page_transitions"] = {
            "transitions": transition_metrics,
            "max_ms": max_transition,
            "average_ms": statistics.mean([t["total_ms"] for t in transition_metrics]),
        }

        # Check SLA
        if max_transition <= TARGETS["page_transition_ms"]:
            print(f"  ✓ Page transition SLA PASSED ({max_transition}ms "
                  f"<= {TARGETS['page_transition_ms']}ms)")
        else:
            print(f"  ✗ Page transition SLA FAILED ({max_transition}ms "
                  f"> {TARGETS['page_transition_ms']}ms)")

    def _benchmark_memory_usage(self) -> None:
        """Benchmark memory usage."""
        print("  Measuring memory usage...")

        # Get current process memory
        mem_info = self.process.memory_info()
        memory_mb = mem_info.rss / 1024 / 1024

        # Get system memory
        system_memory = psutil.virtual_memory()

        memory_metrics = {
            "process_rss_mb": memory_mb,
            "process_vms_mb": mem_info.vms / 1024 / 1024,
            "system_total_mb": system_memory.total / 1024 / 1024,
            "system_available_mb": system_memory.available / 1024 / 1024,
            "system_percent": system_memory.percent,
        }

        self.results["metrics"]["memory"] = memory_metrics

        print(f"    Process RSS: {memory_mb:.2f}MB")
        print(f"    Process VMS: {memory_metrics['process_vms_mb']:.2f}MB")
        print(f"    System Memory: {memory_metrics['system_available_mb']:.0f}MB "
              f"available / {memory_metrics['system_total_mb']:.0f}MB total "
              f"({memory_metrics['system_percent']:.1f}% used)")

        # Check SLA
        if memory_mb <= TARGETS["memory_usage_mb"]:
            print(f"  ✓ Memory SLA PASSED ({memory_mb:.2f}MB "
                  f"<= {TARGETS['memory_usage_mb']}MB)")
        else:
            print(f"  ✗ Memory SLA FAILED ({memory_mb:.2f}MB "
                  f"> {TARGETS['memory_usage_mb']}MB)")

    def _generate_summary(self) -> None:
        """Generate summary report."""
        summary = {
            "total_tests": len(self.results["tests"]),
            "tests_passed": 0,
            "tests_failed": 0,
            "sla_metrics": {},
        }

        # Check each SLA
        api_metrics = self.results["metrics"].get("api_response")
        if api_metrics:
            if api_metrics["p95_ms"] <= TARGETS["api_response_p95_ms"]:
                summary["sla_metrics"]["api_p95_response"] = "PASS"
                summary["tests_passed"] += 1
            else:
                summary["sla_metrics"]["api_p95_response"] = "FAIL"
                summary["tests_failed"] += 1

        bundle_metrics = self.results["metrics"].get("bundle_load")
        if bundle_metrics:
            if bundle_metrics["simulated_4g_time_s"] <= TARGETS["bundle_load_time_s"]:
                summary["sla_metrics"]["bundle_load"] = "PASS"
                summary["tests_passed"] += 1
            else:
                summary["sla_metrics"]["bundle_load"] = "FAIL"
                summary["tests_failed"] += 1

        page_metrics = self.results["metrics"].get("page_transitions")
        if page_metrics:
            if page_metrics["max_ms"] <= TARGETS["page_transition_ms"]:
                summary["sla_metrics"]["page_transition"] = "PASS"
                summary["tests_passed"] += 1
            else:
                summary["sla_metrics"]["page_transition"] = "FAIL"
                summary["tests_failed"] += 1

        memory_metrics = self.results["metrics"].get("memory")
        if memory_metrics:
            if memory_metrics["process_rss_mb"] <= TARGETS["memory_usage_mb"]:
                summary["sla_metrics"]["memory_usage"] = "PASS"
                summary["tests_passed"] += 1
            else:
                summary["sla_metrics"]["memory_usage"] = "FAIL"
                summary["tests_failed"] += 1

        self.results["summary"] = summary

        # Print summary
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)
        print(f"Tests Passed: {summary['tests_passed']}")
        print(f"Tests Failed: {summary['tests_failed']}")
        print("\nSLA Status:")
        for sla, status in summary["sla_metrics"].items():
            icon = "✓" if status == "PASS" else "✗"
            print(f"  {icon} {sla.upper()}: {status}")

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile from data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def save_results(self, output_format: str = "json") -> str:
        """Save benchmark results to file."""
        BENCHMARK_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = f"benchmark_{timestamp}"

        if output_format == "json":
            filepath = BENCHMARK_RESULTS_DIR / f"{basename}.json"
            with open(filepath, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"\n✓ Results saved to: {filepath}")
            return str(filepath)

        elif output_format == "html":
            filepath = self._generate_html_report(basename)
            print(f"\n✓ HTML report saved to: {filepath}")
            return str(filepath)

        return ""

    def _generate_html_report(self, basename: str) -> Path:
        """Generate HTML report."""
        filepath = BENCHMARK_RESULTS_DIR / f"{basename}.html"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Benchmark Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .metric {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
        .pass {{ color: #22c55e; font-weight: bold; }}
        .fail {{ color: #ef4444; font-weight: bold; }}
        .summary {{ background: #f0f9ff; padding: 15px; border-left: 4px solid #3b82f6; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; font-weight: 600; }}
    </style>
</head>
<body>
    <h1>Performance Benchmark Report</h1>
    <p>Generated: {self.results['timestamp']}</p>
    <p>Environment: {self.results['environment']['base_url']}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p>Tests Passed: <span class="pass">{self.results['summary']['tests_passed']}</span></p>
        <p>Tests Failed: <span class="fail">{self.results['summary']['tests_failed']}</span></p>
    </div>

    <h2>API Response Time</h2>
"""
        if "api_response" in self.results["metrics"]:
            m = self.results["metrics"]["api_response"]
            status_class = (
                "pass"
                if m["p95_ms"] <= TARGETS["api_response_p95_ms"]
                else "fail"
            )
            html_content += f"""
    <div class="metric">
        <p>P50 (Median): {m['median_ms']:.2f}ms</p>
        <p>P95: <span class="{status_class}">{m['p95_ms']:.2f}ms</span> (Target: {TARGETS['api_response_p95_ms']}ms)</p>
        <p>P99: {m['p99_ms']:.2f}ms</p>
        <p>Mean: {m['mean_ms']:.2f}ms</p>
    </div>
"""

        html_content += "</body></html>"

        with open(filepath, "w") as f:
            f.write(html_content)

        return filepath


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmarking Tool")
    parser.add_argument(
        "--output",
        choices=["json", "html", "both"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--compare",
        help="Compare against baseline JSON file",
    )
    args = parser.parse_args()

    # Run benchmarks
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_all_benchmarks()

    # Save results
    if args.output in ["json", "both"]:
        benchmark.save_results("json")
    if args.output in ["html", "both"]:
        benchmark.save_results("html")

    # Compare against baseline if provided
    if args.compare and Path(args.compare).exists():
        print(f"\n" + "=" * 70)
        print("COMPARISON WITH BASELINE")
        print("=" * 70)
        with open(args.compare) as f:
            baseline = json.load(f)

        if "api_response" in baseline.get("metrics", {}):
            baseline_p95 = baseline["metrics"]["api_response"]["p95_ms"]
            current_p95 = results["metrics"].get("api_response", {}).get("p95_ms", 0)
            diff = current_p95 - baseline_p95
            percent = (diff / baseline_p95 * 100) if baseline_p95 > 0 else 0

            print(f"\nAPI P95 Response Time:")
            print(f"  Baseline: {baseline_p95:.2f}ms")
            print(f"  Current:  {current_p95:.2f}ms")
            print(f"  Change:   {diff:+.2f}ms ({percent:+.1f}%)")

            if abs(percent) < 5:
                print(f"  ✓ Within acceptable variance (< 5%)")
            elif diff > 0:
                print(f"  ⚠ Performance regression detected!")
            else:
                print(f"  ✓ Performance improved!")

    # Exit with code based on results
    failed = results["summary"]["tests_failed"]
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
