
import os
import sys
import uvicorn

# Add the current directory to sys.path to resolve 'src' imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
