"""
Load testing suite for Digital FTE Customer Success Agent (T122).
Simulates high-concurrency bursts to ensure p95 latency and reliability under load.
Simulates: 100+ web, 50+ gmail, 50+ whatsapp messages per hour (Total ~200/hr).
Test Scenario: Concurrent burst of 20 requests across all channels.
"""
import asyncio
import time
import logging
import random
from typing import List, Dict, Any
from src.services.inquiry_processor import create_inquiry_processor
from src.services.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def simulate_channel_inquiry(processor, channel: str, index: int) -> Dict[str, Any]:
    """Simulate a single inquiry on a specific channel."""
    message_bodies = [
        "Hi, I am having trouble with the API integration. Error 500.",
        "Could you please explain the monthly billing cycle?",
        "I need to cancel my subscription and get a refund.",
        "What are the latest features in the factory portal?",
        "The web form is not submitting. Please help ASAP!"
    ]
    
    start_time = time.time()
    raw_message = {
        "text": random.choice(message_bodies),
        "sender": f"customer_{index}@example.com" if channel != 'whatsapp' else f"+1555000{index:03d}",
        "subject": f"Inquiry #{index} via {channel}"
    }
    
    try:
        result = await processor.process_inquiry(raw_message, channel)
        latency = time.time() - start_time
        return {
            "success": result.get("success", False),
            "latency": latency,
            "channel": channel,
            "index": index
        }
    except Exception as e:
        logger.error(f"Error in load test request {index} ({channel}): {e}")
        return {"success": False, "latency": time.time() - start_time, "error": str(e)}

async def run_load_test(concurrency: int = 20):
    """Run a high-concurrency load test."""
    init_db()
    processor = create_inquiry_processor()
    
    logger.info(f"--- Starting Load Test (Concurrency: {concurrency}) ---")
    
    # Mix of channels based on load spec (100:50:50 ratio = 2:1:1)
    channels = (['webform'] * 10) + (['email'] * 5) + (['whatsapp'] * 5)
    
    start_time = time.time()
    tasks = []
    for i in range(concurrency):
        channel = channels[i % len(channels)]
        tasks.append(simulate_channel_inquiry(processor, channel, i))
    
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # Calculate metrics
    latencies = [r['latency'] for r in results]
    successes = [r for r in results if r['success']]
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    
    logger.info(f"--- Load Test Results ---")
    logger.info(f"Total Requests: {len(results)}")
    logger.info(f"Successes: {len(successes)} ({len(successes)/len(results)*100:.1f}%)")
    logger.info(f"Total Time: {total_time:.3f}s")
    logger.info(f"Average Latency: {avg_latency:.3f}s")
    logger.info(f"P95 Latency: {p95_latency:.3f}s")
    logger.info(f"Throughput: {len(results)/total_time:.2f} req/s")
    
    if p95_latency < 3.0:
        logger.info("Load Test: PASSED (<3s p95)")
    else:
        logger.info("Load Test: FAILED (>3s p95)")

if __name__ == "__main__":
    asyncio.run(run_load_test())
