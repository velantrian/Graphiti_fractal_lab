import asyncio
import os
import sys
from pathlib import Path
import random
import string
import logging

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stability_test")

def generate_large_text(size=30000):
    return "".join(random.choices(string.ascii_letters + " ", k=size))

async def main():
    print("=== STARTING STABILITY TEST ===")
    
    # 1. Generate large file
    # Reduced size slightly to be faster but still significant
    large_text = generate_large_text(25000)
    print(f"Generated text size: {len(large_text)}")
    
    try:
        import httpx
    except ImportError:
        print("httpx not found, installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
        import httpx

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=60.0) as client:
        
        # Check if server is running
        try:
            r = await client.get("/docs")
            if r.status_code != 200:
                print("Server not responding correctly on localhost:8000. Is it running?")
                # We can't easily start the server from here as a background process and wait for it 
                # within the same script if we want to capture output nicely, 
                # but we can assume the user or environment has it running or we use TestClient.
                # However, TestClient with async requires usage of the app object.
                raise Exception("Server not reachable")
        except Exception as e:
            print(f"Server check failed: {e}")
            print("Using FastAPI TestClient as fallback (in-process server)")
            
            from fastapi.testclient import TestClient
            from api import app
            
            # wrapper for TestClient to look like async client
            class AsyncTestClientWrapper:
                def __init__(self, app):
                    self.client = TestClient(app)
                
                async def post(self, url, **kwargs):
                    # TestClient is sync, so we just call it
                    return self.client.post(url, **kwargs)
                
                async def get(self, url, **kwargs):
                    return self.client.get(url, **kwargs)
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, exc_type, exc, tb):
                    pass
            
            client = AsyncTestClientWrapper(app)

        # 2. Start Upload
        print("Starting upload...")
        # For TestClient, files need to be handled carefully
        # For httpx/TestClient:
        files = {'file': ('large.txt', large_text, 'text/plain')}
        data = {'source_description': 'stress_test', 'memory_type': 'knowledge', 'user_id': 'sergey'}
        
        resp = await client.post("/upload", files=files, data=data)
        if resp.status_code != 200:
            print(f"Upload failed: {resp.status_code} {resp.text}")
            return
        
        job_id = resp.json()['job_id']
        print(f"Upload started, job_id={job_id}")
        
        # 3. Send parallel chat messages
        print("Sending chat messages...")
        
        async def send_chat(i):
            msg = f"Chat message {i} during upload"
            print(f"  Sending chat {i}...")
            # Use a slightly long message to trigger some processing but not the long-message limit
            r = await client.post("/chat", json={"message": msg, "user_id": "sergey"})
            print(f"  Chat {i} status: {r.status_code}")
            return r.json()

        # Launch chat tasks
        chat_tasks = [send_chat(i) for i in range(1, 4)]
        
        # We need to await them. 
        # Note: If using TestClient (sync), these will actually run sequentially in this loop 
        # because the wrapper calls sync methods.
        # But if the server handles them in background (like upload), it still tests the concurrency on the server side 
        # (mostly for the background tasks created by the endpoints).
        
        chat_results = await asyncio.gather(*chat_tasks)
        print("Chat messages sent.")
        
        # 4. Monitor upload job
        while True:
            r = await client.get(f"/upload/status/{job_id}")
            status = r.json()
            stage = status.get('stage')
            print(f"Upload job status: {stage}")
            
            if stage in ['done', 'error']:
                if stage == 'error':
                    print(f"❌ Upload failed: {status.get('error')}")
                else:
                    print(f"✅ Upload finished successfully. Timing: {status.get('profile')}")
                break
            
            await asyncio.sleep(1)

    print("=== TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(main())
