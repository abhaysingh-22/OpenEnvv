"""Debug script to see what actions agents are taking."""
import sys
sys.path.insert(0, '/Users/abhaysingh22_/Developer/OpenEnv')

from validate_scoring import PerfectAgent, ImperfectAgent, RandomAgent
from env import models
import json

def test_agent_actions():
    """Test what actions agents take for easy task."""
    print("Testing Easy Task Actions")
    print("=" * 60)
    
    # Test ImperfectAgent 5 times with more detail
    print("\nImperfect Agent (Easy task) - 5 detailed runs:")
    for run in range(5):
        agent = ImperfectAgent()
        
        # Simulate easy task observation
        obs = {"customer_issue": "Password reset request", "content": "Can't reset my password"}
        print(f"\n  Run {run+1}:")
        print(f"    Observation: {obs}")
        print(f"    Agent task type before act: {agent.task_type if hasattr(agent, 'task_type') else 'N/A'}")
        
        # Step 1
        action1 = agent.act(obs)
        print(f"    After step 1: task_type={agent.task_type}, action={action1.tool_name}")
        
        # Step 2
        action2 = agent.act(obs)
        print(f"    After step 2: action={action2.tool_name}")
        
        agent.reset()

if __name__ == "__main__":
    test_agent_actions()

