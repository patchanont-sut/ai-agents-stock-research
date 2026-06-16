"""Test the full orchestration pipeline end-to-end."""
import asyncio
import sys
import logging
import time

sys.path.insert(0, "backend")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from core.orchestrator import Orchestrator
from core.memory import cleanup_memory

async def main():
    symbol = "AAPL"
    session_id = "test-session-001"
    
    print("=" * 60)
    print(f"FULL PIPELINE TEST: {symbol}")
    print("=" * 60)
    
    orch = Orchestrator(symbol=symbol, session_id=session_id)
    start = time.time()
    
    try:
        result = await orch.run_pipeline()
        elapsed = time.time() - start
        
        print(f"\nPipeline complete in {elapsed:.1f}s")
        print(f"Status: {result.status.value}")
        print(f"Errors: {result.errors}")
        print(f"CIO Decision: {result.cio_decision.action.value if result.cio_decision else 'NONE'}")
        print(f"Sentiment: {result.sentiment.overall_score if result.sentiment else 'NONE'}")
        print(f"Bull Case: {result.bull_case.thesis[:100] if result.bull_case and result.bull_case.thesis else 'NONE'}")
        print(f"Bear Case: {result.bear_case.thesis[:100] if result.bear_case and result.bear_case.thesis else 'NONE'}")
        print(f"News articles: {len(result.research.news_articles) if result.research else 0}")
        print(f"Reddit posts: {len(result.research.reddit_posts) if result.research else 0}")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"\nPipeline FAILED after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_memory(session_id)

if __name__ == "__main__":
    asyncio.run(main())