"""
Performance benchmarking script for Digital FTE AI Customer Success Agent.
Measures end-to-end latency of the inquiry processing pipeline.
"""
import asyncio
import time
import logging
import statistics
from typing import Dict, Any, List

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from src.services.inquiry_processor import InquiryProcessor, create_inquiry_processor
from src.services.database import init_db

async def benchmark_inquiry_processing(num_requests: int = 10, channel: str = "webform"):
    """
    Run a performance benchmark for the inquiry processor.
    
    Args:
        num_requests: Number of requests to process for the benchmark.
        channel: The channel to simulate (e.g., 'email', 'whatsapp', 'webform').
    """
    # Ensure database is initialized for the benchmark
    init_db()
    
    processor = create_inquiry_processor()
    # Initialize the processor (this will also initialize its dependencies)
    await processor.initialize()
    
    # Sample messages for testing
    test_messages = [
        {"subject": "Pricing inquiry", "body": "How much does the standard plan cost?"},
        {"subject": "Integration issue", "body": "I'm having trouble connecting my API key."},
        {"subject": "Account reset", "body": "Please reset my password, I can't log in."},
        {"subject": "Refund request", "body": "I'd like a refund for my last month's subscription."},
        {"subject": "Feature request", "body": "Do you support dark mode on the dashboard?"}
    ]
    
    latencies = []
    
    logger.info(f"Starting benchmark: {num_requests} requests on channel '{channel}'...")
    
    for i in range(num_requests):
        msg = test_messages[i % len(test_messages)]
        start_time = time.time()
        
        try:
            result = await processor.process_inquiry(msg, channel)
            duration = time.time() - start_time
            latencies.append(duration)
            logger.info(f"Request {i+1}/{num_requests} completed in {duration:.3f}s (Success: {result.get('success')})")
        except Exception as e:
            logger.error(f"Error during request {i+1}: {e}")
            
    if not latencies:
        logger.error("No successful requests to calculate metrics.")
        return
        
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    logger.info("\n--- Benchmark Results ---")
    logger.info(f"Total Requests: {num_requests}")
    logger.info(f"Average Latency: {avg_latency:.3f}s")
    logger.info(f"P95 Latency: {p95_latency:.3f}s")
    logger.info(f"Min Latency: {min_latency:.3f}s")
    logger.info(f"Max Latency: {max_latency:.3f}s")
    
    target_met = p95_latency < 3.0
    logger.info(f"Performance Requirement (<3s p95): {'PASSED' if target_met else 'FAILED'}")
    
    return {
        "avg": avg_latency,
        "p95": p95_latency,
        "min": min_latency,
        "max": max_latency,
        "target_met": target_met
    }

if __name__ == "__main__":
    # Ensure the script can be run directly
    import os
    import sys
    # Add backend/src to path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
    
    asyncio.run(benchmark_inquiry_processing(num_requests=5))
