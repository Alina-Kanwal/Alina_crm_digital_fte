"""
Load testing suite for Digital FTE Agent.
Tests Constitution FR-027: Process 100+ web forms, 50+ Gmail, 50+ WhatsApp messages per hour.
"""
import asyncio
import aiohttp
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics
from dataclasses import dataclass


@dataclass
class TestConfig:
    """Configuration for load test."""
    name: str
    target_rate: int  # Requests per hour
    duration: int  # Test duration in seconds
    concurrent_users: int
    base_url: str


@dataclass
class TestResult:
    """Result of load test."""
    name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    target_met: bool
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    duration_seconds: float
    actual_rph: int  # Actual requests per hour


class LoadTester:
    """Load testing framework for Digital FTE Agent."""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = None
        self.results = {}

    async def __aenter__(self):
        """Initialize session."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session."""
        if self.session:
            await self.session.close()

    def _generate_test_data(self, channel: str, count: int) -> List[Dict[str, Any]]:
        """Generate test data for the specified channel."""
        test_data = []

        for i in range(count):
            if channel == 'webform':
                data = {
                    'channel': 'webform',
                    'customer_email': f'loadtest{i}@example.com',
                    'customer_name': f'Load Test User {i}',
                    'message': self._get_random_message(),
                    'session_id': f'load-test-session-{i}'
                }
            elif channel == 'email':
                data = {
                    'channel': 'email',
                    'customer_email': f'loadtest{i}@example.com',
                    'subject': f'Load Test Subject {i}',
                    'message': self._get_random_message()
                }
            elif channel == 'whatsapp':
                data = {
                    'channel': 'whatsapp',
                    'customer_phone': f'+1555555{i:04d}',
                    'sender_id': f'wa-load-test-{i}',
                    'message': self._get_random_message()
                }
            else:
                raise ValueError(f"Unknown channel: {channel}")

            test_data.append(data)

        return test_data

    def _get_random_message(self) -> str:
        """Generate random test messages."""
        messages = [
            "How do I integrate with Slack?",
            "I need help setting up workflows.",
            "What's the pricing for enterprise plans?",
            "My authentication is failing, help!",
            "How do I create automation triggers?",
            "I want to request a refund for my subscription.",
            "Need help with API key setup.",
            "What are the steps for OAuth configuration?",
            "Can you explain the workflow execution process?"
        ]
        return random.choice(messages)

    async def submit_webform_inquiry(
        self,
        data: Dict[str, Any],
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Submit web form inquiry."""
        url = f"{self.base_url}/inquiries"
        start_time = time.time()

        try:
            async with session.post(url, json=data, timeout=10) as response:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'status_code': response.status,
                        'latency_ms': latency_ms,
                        'ticket_id': result.get('ticket_id'),
                        'message': result.get('message', '')
                    }
                else:
                    return {
                        'success': False,
                        'status_code': response.status,
                        'latency_ms': latency_ms,
                        'error': f"HTTP {response.status}"
                    }
        except asyncio.TimeoutError:
            return {
                'success': False,
                'status_code': None,
                'latency_ms': 10000,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'latency_ms': 10000,
                'error': str(e)
            }

    async def submit_email_inquiry(
        self,
        data: Dict[str, Any],
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Submit email inquiry."""
        url = f"{self.base_url}/inquiries"
        start_time = time.time()

        try:
            async with session.post(url, json=data, timeout=10) as response:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'status_code': response.status,
                        'latency_ms': latency_ms,
                        'ticket_id': result.get('ticket_id'),
                        'message': result.get('message', '')
                    }
                else:
                    return {
                        'success': False,
                        'status_code': response.status,
                        'latency_ms': latency_ms,
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'latency_ms': 10000,
                'error': str(e)
            }

    async def submit_whatsapp_inquiry(
        self,
        data: Dict[str, Any],
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Submit WhatsApp inquiry."""
        url = f"{self.base_url}/inquiries"
        start_time = time.time()

        try:
            async with session.post(url, json=data, timeout=10) as response:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'status_code': response.status,
                        'latency_ms': latency_ms,
                        'ticket_id': result.get('ticket_id'),
                        'message': result.get('message', '')
                    }
                else:
                    return {
                        'success': False,
                        'status_code': response.status,
                        'latency_ms': latency_ms,
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'latency_ms': 10000,
                'error': str(e)
            }

    async def run_test(
        self,
        config: TestConfig
    ) -> TestResult:
        """Run a single load test."""
        print(f"\n{'='*80}")
        print(f"Starting: {config.name}")
        print(f"Target: {config.target_rate} requests/hour")
        print(f"Duration: {config.duration} seconds")
        print(f"{'='*80}\n")

        # Generate test data
        if 'webform' in config.name.lower():
            channel = 'webform'
        elif 'email' in config.name.lower():
            channel = 'email'
        elif 'whatsapp' in config.name.lower():
            channel = 'whatsapp'
        else:
            raise ValueError(f"Unknown test: {config.name}")

        test_data = self._generate_test_data(channel, config.target_rate)

        # Calculate requests per second for desired rate
        rps = config.target_rate / 3600  # requests per second

        # Calculate delay between requests
        delay = 1.0 / rps if rps > 0 else 0

        # Track metrics
        start_time = time.time()
        results = []
        completed_requests = 0

        print(f"Generating {len(test_data)} test requests...")

        try:
            # Create session for this test
            async with aiohttp.ClientSession() as session:
                # Submit all requests
                tasks = []
                for i, data in enumerate(test_data):
                    if channel == 'webform':
                        task = self.submit_webform_inquiry(data, session)
                    elif channel == 'email':
                        task = self.submit_email_inquiry(data, session)
                    else:  # whatsapp
                        task = self.submit_whatsapp_inquiry(data, session)
                    tasks.append(task)

                    # Process in batches to maintain target rate
                    if (i + 1) % config.concurrent_users == 0:
                        batch_results = await asyncio.gather(*tasks)
                        results.extend(batch_results)
                        completed_requests += len(batch_results)
                        tasks.clear()

                        # Calculate delay to maintain rate
                        elapsed = time.time() - start_time
                        expected_time = completed_requests / rps
                        if elapsed < expected_time:
                            sleep_time = expected_time - elapsed
                            if sleep_time > 0:
                                await asyncio.sleep(sleep_time)

                # Process remaining tasks
                if tasks:
                    remaining_results = await asyncio.gather(*tasks)
                    results.extend(remaining_results)
                    completed_requests += len(remaining_results)

        except asyncio.CancelledError:
            print(f"\n{'='*80}")
            print(f"Test {config.name} CANCELLED")
            print(f"{'='*80}\n")
            raise
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"Test {config.name} FAILED: {e}")
            print(f"{'='*80}\n")
            raise

        # Calculate statistics
        end_time = time.time()
        total_duration = end_time - start_time
        actual_rph = (completed_requests / total_duration) * 3600 if total_duration > 0 else 0

        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        latencies = [r['latency_ms'] for r in results if r['success']]
        success_rate = len(successful) / len(results) if results else 0

        result = TestResult(
            name=config.name,
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            success_rate=success_rate * 100,
            target_met=len(successful) >= config.target_rate * 0.95,  # 95% of target
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=statistics.median(latencies) if latencies else 0,
            p95_latency_ms=statistics.quantiles(latencies, n=10)[8] if len(latencies) > 9 else 0,
            p99_latency_ms=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 99 else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            duration_seconds=total_duration,
            actual_rph=actual_rph
        )

        # Print results
        self._print_test_results(result)

        return result

    def _print_test_results(self, result: TestResult):
        """Print formatted test results."""
        print(f"\n{'='*80}")
        print(f"RESULTS: {result.name}")
        print(f"{'='*80}\n")

        print(f"Total Requests:      {result.total_requests}")
        print(f"Successful:         {result.successful_requests} ({result.success_rate:.1f}%)")
        print(f"Failed:             {result.failed_requests}")

        if result.successful_requests > 0:
            print(f"\nLatency Metrics (ms):")
            print(f"  Average:          {result.avg_latency_ms:.0f}")
            print(f"  P50 (Median):     {result.p50_latency_ms:.0f}")
            print(f"  P95:              {result.p95_latency_ms:.0f}")
            print(f"  P99:              {result.p99_latency_ms:.0f}")
            print(f"  Min:              {result.min_latency_ms:.0f}")
            print(f"  Max:              {result.max_latency_ms:.0f}")

        print(f"\nPerformance:")
        print(f"  Duration:         {result.duration_seconds:.1f}s")
        print(f"  Actual Rate:      {result.actual_rph:.0f} requests/hour")
        print(f"  Target Rate:      100 requests/hour")  # Based on config

        print(f"\nValidation:")
        target_met = "✅ PASSED" if result.target_met else "❌ FAILED"
        print(f"  Target Met:       {target_met}")

        p95_ok = "✅ PASSED" if result.p95_latency_ms < 3000 else "❌ FAILED (>3s)"
        print(f"  Latency <3s (P95): {p95_ok}")

        print(f"{'='*80}\n")

    def print_summary(self, results: List[TestResult]):
        """Print summary of all test results."""
        print(f"\n{'='*80}")
        print(f"LOAD TEST SUMMARY")
        print(f"{'='*80}\n")

        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        total_failed = sum(r.failed_requests for r in results)

        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0

        print(f"\nOverall:")
        print(f"  Total Requests:   {total_requests}")
        print(f"  Successful:        {total_successful} ({overall_success_rate:.1f}%)")
        print(f"  Failed:           {total_failed}")

        all_targets_met = all(r.target_met for r in results)
        print(f"\nConstitution Compliance:")
        print(f"  All Targets Met:  {'✅ YES' if all_targets_met else '❌ NO'}")

        print(f"\n{'='*80}\n")

        # Check specific requirements
        webform_target = 100
        email_target = 50
        whatsapp_target = 50

        for result in results:
            target = 0
            if 'webform' in result.name.lower():
                target = webform_target
            elif 'email' in result.name.lower():
                target = email_target
            elif 'whatsapp' in result.name.lower():
                target = whatsapp_target

            met = result.actual_rph >= target
            status = "✅ PASSED" if met else "❌ FAILED"
            print(f"{result.name}: {status} (Target: {target}, Actual: {result.actual_rph:.0f})")


async def main():
    """Main entry point for load testing."""
    async with LoadTester() as tester:
        # Define test configurations
        tests = [
            TestConfig(
                name="Web Form High Load Test",
                target_rate=100,  # 100 forms/hour
                duration=60,  # 1 minute test
                concurrent_users=5,
                base_url=tester.base_url
            ),
            TestConfig(
                name="Email Load Test",
                target_rate=50,  # 50 emails/hour
                duration=60,
                concurrent_users=3,
                base_url=tester.base_url
            ),
            TestConfig(
                name="WhatsApp Load Test",
                target_rate=50,  # 50 messages/hour
                duration=60,
                concurrent_users=3,
                base_url=tester.base_url
            ),
        ]

        print("🚀 Digital FTE Agent Load Testing Suite")
        print("=" * 80)
        print("\nThis will test Constitution FR-027:")
        print("- 100+ web form submissions per hour")
        print("- 50 Gmail messages per hour")
        print("- 50 WhatsApp messages per hour")
        print("\nTarget: <3s response latency (p95)")
        print("=" * 80)

        # Run tests sequentially
        results = []
        for test_config in tests:
            try:
                result = await tester.run_test(test_config)
                results.append(result)

                # Small delay between tests
                await asyncio.sleep(5)

            except Exception as e:
                print(f"Test failed with error: {e}")
                continue

        # Print summary
        tester.print_summary(results)

        print("\n" + "=" * 80)
        print("LOAD TESTING COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    import sys

    # Allow command line arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/v1"

    print(f"Testing against: {base_url}")
    print(f"Use Ctrl+C to cancel\n")

    asyncio.run(main())
