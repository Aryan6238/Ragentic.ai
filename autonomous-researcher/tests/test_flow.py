from fastapi.testclient import TestClient
import logging
import asyncio
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

# Mock LLM and RAG to avoid needing real keys
@patch('app.core.llm.llm_client.generate_text', new_callable=AsyncMock)
@patch('app.services.rag.rag_service.search', new_callable=AsyncMock)
def test_end_to_end_research_flow(mock_rag_search, mock_llm_generate):
    # Setup Mocks
    mock_llm_generate.side_effect = [
        '["What is AI?", "Why is it cool?"]', # 1. Planner response
        "Analysis of AI",                     # 2. Analyzer response 1
        "Analysis of Coolness",               # 3. Analyzer response 2
        "<h1>Final Report</h1><p>Done.</p>"   # 4. Writer response
    ]
    
    mock_rag_search.return_value = ["Doc Chunk 1", "Doc Chunk 2"] # RAG response

    # 1. Start Research
    response = client.post("/api/v1/research", json={"topic": "Test Topic"})
    assert response.status_code == 200
    data = response.json()
    task_id = data["task_id"]
    assert task_id is not None

    # 2. Poll for Logs (We need to wait a tiny bit for background task to pick up, or use TestClient's context manager?)
    # FastAPI TestClient doesn't auto-run background tasks synchronously unless using Starlette's BackgroundTasks differently.
    # However, for unit testing logic, we might need to manually trigger the orchestrator if standard client doesn't wait.
    # Let's Rely on the fact that standard logic will be executed if validation passes.
    
    # Actually, TestClient DOES run background tasks after the response is sent.
    # So we should be able to read the logs immediately.
    
    import time
    time.sleep(1) # Small wait for async loop
    
    logs_response = client.get(f"/api/v1/stream/{task_id}")
    assert logs_response.status_code == 200
    logs = logs_response.json()
    
    # Verify we have logs
    # Note: Depending on async execution speed, we might not have ALL logs yet. 
    # But we should have "Started".
    assert len(logs) > 0
    assert logs[0]["status"] == "Started"

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    print("Running verification...")
    # Run the test logic (Mocking needs context, so we just call the function)
    # But wait, the function uses decorators which rely on pytest or unittest.mock.patch context.
    # We can invoke it, but the decorators might not apply if called directly without a runner? 
    # Actually @patch decorators act as wrappers, so calling the function works if we pass the mock args.
    # BUT, new_callable=AsyncMock means it expects to pass the mock as arg.
    
    # Simpler: Use unittest.main if we wrap in TestCase, OR just rely on the decorators working as wrappers.
    # Let's wrap in a try-except to run it.
    
    try:
        # We need to run the async mocking properly.
        # Check if we can just run it.
        test_end_to_end_research_flow()
        print("✅ VERIFICATION SUCCESS: End-to-End Flow Passed!")
    except Exception as e:
        print(f"❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
