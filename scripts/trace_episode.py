"""Debug script to trace through environment and grading."""
import sys
sys.path.insert(0, '/Users/abhaysingh22_/Developer/OpenEnv')

from validate_scoring import ImperfectAgent, PerfectAgent
from tasks import EasyTask
from graders.support_grader import SupportGrader
from env.environment import Environment
import random

def trace_episode(agent_class, agent_name, num_runs=3):
    """Trace episodes with detailed reward logging."""
    print(f"\n{'='*70}")
    print(f"Testing {agent_name} on Easy Task ({num_runs} runs)")
    print('='*70)
    
    for run in range(num_runs):
        print(f"\n--- Run {run+1} ---")
        
        # Create environment
        task = EasyTask(
            task_id="easy_ticket_1",
            title="Password Reset",
            description="Customer needs password reset"
        )
        grader = SupportGrader()
        env = Environment(task, grader, max_steps=20)
        
        # Reset and get initial state
        agent = agent_class()
        state = env.reset()
        
        total_reward = 0.0
        step_num = 0
        actions_taken = []
        
        for step in range(20):
            step_num += 1
            
            # Get action from agent
            action = agent.act(state)
            actions_taken.append(action.tool_name)
            print(f"  Step {step_num}: action={action.tool_name}")
            
            # Step environment
            state, reward_obj, done, info = env.step(action)
            
            # Log reward
            reward_val = reward_obj.value if hasattr(reward_obj, 'value') else 0.0
            print(f"    -> score={reward_val:.3f}, info={reward_obj.info if hasattr(reward_obj, 'info') else ''}")
            
            total_reward = reward_val
            
            if done:
                break
        
        print(f"  Final score: {total_reward:.3f}")
        print(f"  Actions: {' → '.join(actions_taken)}")

if __name__ == "__main__":
    # Seed to get a run where imperfect makes a mistake
    random.seed(42)
    trace_episode(PerfectAgent, "PerfectAgent", num_runs=2)
    
    random.seed(99)  # Different seed to find imperfect mistake
    trace_episode(ImperfectAgent, "ImperfectAgent", num_runs=3)
