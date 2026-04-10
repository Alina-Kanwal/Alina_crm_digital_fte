import os
import asyncio
import litellm
from dotenv import load_dotenv

async def smoke_test():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")
    base_url = os.getenv("GROQ_API_BASE")
    
    print(f"MODEL: {model}")
    print(f"BASE_URL: {base_url}")
    print("Connecting to GROQ...")
    
    try:
        # Standardize model name if needed
        test_model = model
        if test_model.startswith("groq/"):
            test_model = test_model.replace("groq/", "")
            
        print(f"TESTING WITH: groq/{test_model}")
        
        response = await litellm.acompletion(
            model=f"groq/{test_model}",
            messages=[{"role": "user", "content": "Hello! Rapid confirmation needed."}],
            api_key=api_key
        )
        print("\nSUCCESS! RESPONSE FROM GROQ:")
        print("-" * 30)
        print(response.choices[0].message.content)
        print("-" * 30)
    except Exception as e:
        print(f"\nERROR OCCURRED: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(smoke_test())
