"""Direct test of score differentiation."""
import sys
sys.path.insert(0, '/Users/abhaysingh22_/Developer/OpenEnv')

from validate_scoring import PerfectAgent, ImperfectAgent, RandomAgent
from tasks import EasyTask, MediumTask, HardTask
from graders.support_grader import SupportGrader
from env.environment import Environment

def test_direct_scoring():
    """Run agents through environment and check actual scores."""
    
    print("="*70)
    print("DIRECT SCORING TEST - 10 runs each task")
    print("="*70)
    
    tasks = {
        'easy': (EasyTask(task_id="easy_ticket_1", title="Password Reset", description="User needs password reset"), "Easy"),
        'medium': (MediumTask(task_id="medium_ticket_1", title="Refund Request", description="Customer requesting refund"), "Medium"),
        'hard': (HardTask(task_id="hard_ticket_1", title="Technical Error", description="API returning 500 error"), "Hard"),
    }
    
    for task_key, (task_template, task_name) in tasks.items():
        print(f"\n{task_name.upper()} TASK - 10 episodes")
        print("-" * 70)
        
        for agent_class, agent_name in [(PerfectAgent, "Perfect"), (ImperfectAgent, "Imperfect"), (RandomAgent, "Random")]:
            scores = []
            
            for episode in range(10):
                task = task_template.__class__(
                    task_id=task_template.task_id,
                    title=task_template.title,
                    description=task_template.description
                )
                grader = SupportGrader()
                env = Environment(task, grader, max_steps=20)
                
                agent = agent_class()
                state = env.reset()
                final_score = 0.0
                
                for step in range(20):
                    action = agent.act(state)
                    state, reward_obj, done, info = env.step(action)
                    final_score = reward_obj.value if hasattr(reward_obj, 'value') else 0.0
                    if done:
                        break
                
                scores.append(final_score)
            
            # Calculate statistics
            mean_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            print(f"  {agent_name:12} - Mean: {mean_score:.3f}, Min: {min_score:.3f}, Max: {max_score:.3f}, Scores: {[f'{s:.2f}' for s in scores]}")

if __name__ == "__main__":
    test_direct_scoring()
