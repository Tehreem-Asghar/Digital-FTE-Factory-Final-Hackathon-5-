import asyncio
import os
import json
from dotenv import load_dotenv
from production.agent.customer_success_agent import customer_success_agent, get_run_config
from agents import Runner

load_dotenv()

async def main():
    config = get_run_config()
    print("Running agent test...")
    try:
        result = await Runner.run(customer_success_agent, "Hi, tell me about subscription tiers", run_config=config)
        print("\n--- Result Attributes ---")
        print(dir(result))
        print(f"\n--- Final Output: '{result.final_output}'")
        
        # Check for history
        for attr in ['messages', 'history', 'steps', 'all_messages']:
            if hasattr(result, attr):
                print(f"\n--- Found Attribute: {attr} ---")
                val = getattr(result, attr)
                if isinstance(val, list):
                    print(f"Count: {len(val)}")
                    if len(val) > 0:
                        # Try to print the last assistant message if possible
                        print("Sample item:", val[-1])
            
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
