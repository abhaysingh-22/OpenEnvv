"""SIMPLIFIED Support grader for OpenEnv.

Simple scoring system:
- Correct action: +0.4
- Correct response: +0.3
- Good tone: +0.2
- Efficiency penalty: -0.1 per extra step
- Wrong action: -0.5
- Repeated action: -0.3
"""
from typing import Any, Dict
from .base_grader import BaseGrader
from env.models import State, Action, Reward
from .rewards import RewardCalculator


class SupportGrader(BaseGrader):
    """Simplified grader with deterministic scoring."""
    
    def __init__(self, answer_key: Dict[str, Any] = None, policy: Dict[str, Any] = None):
        """Initialize grader."""
        super().__init__()
        self.calculator = RewardCalculator()
        
        # Track episode state
        self.task_id = None
        self.step_count = 0
        self.wrong_action_count = 0
        self.last_action = None
        self.min_steps = {
            'easy_ticket_1': 2,
            'medium_ticket_1': 2,
            'hard_ticket_1': 3
        }
        # Track required sequence for hard task
        self.hard_task_sequence = []
    
    def reset_episode(self) -> None:
        """Reset for new episode."""
        self.calculator.reset()
        self.task_id = None
        self.step_count = 0
        self.wrong_action_count = 0
        self.last_action = None
        self.hard_task_sequence = []
    
    def grade(self, state: State, action: Action, is_complete: bool) -> Reward:
        """
        Grade action with simple, deterministic scoring.
        
        Accumulates total_reward and returns normalized final score.
        """
        if not self.task_id:
            self.task_id = state.task_id
        
        self.step_count += 1
        step_reward = 0.0
        info = ""
        
        # ==================== EASY TASK ====================
        if state.task_id == "easy_ticket_1":
            step_reward, info = self._grade_easy(action)
        
        # ==================== MEDIUM TASK ====================
        elif state.task_id == "medium_ticket_1":
            step_reward, info = self._grade_medium(action)
        
        # ==================== HARD TASK ====================
        elif state.task_id == "hard_ticket_1":
            step_reward, info = self._grade_hard(action)
        
        # Apply efficiency penalty for extra steps
        min_steps = self.min_steps.get(state.task_id, 2)
        if self.step_count > min_steps:
            extra = self.step_count - min_steps
            step_reward -= 0.1 * extra
        
        # Accumulate to total reward
        step_reward = max(-0.3, step_reward)  # Don't let single step go too negative
        self.calculator.total_reward += step_reward
        
        # Stop if too many wrong actions (3+)
        if self.wrong_action_count >= 3:
            is_complete = True
        
        # Prevent episode going too long
        if self.step_count > 20:
            is_complete = True
        
        self.scores.append(step_reward)
        self.last_action = action.tool_name  # Track for repeated action penalty
        
        # Calculate final normalized score (for display)
        # Perfect agent gets ~0.9-1.2 per task (0.9 for easy, 1.3 for medium, 2.0 for hard)
        # Use 1.2 as typical max to get 0.8-1.0 range for perfect agent
        max_possible = 1.2
        final_score = max(0.0, min(1.0, self.calculator.total_reward / max_possible))
        
        return Reward(
            value=final_score,
            is_complete=is_complete,
            info=info
        )
    
    def _grade_easy(self, action: Action) -> tuple:
        """Grade easy task (password reset).
        
        Min steps: 2
        - Step 1: send_password_reset → +0.4 (action) +0.3 (response) +0.2 (tone) = 0.9
        - Step 2: close_ticket → +0.3 (action) = 0.3
        """
        if self.step_count == 1:
            if action.tool_name == "send_password_reset":
                if action.tool_args.get("email") == "john@example.com":
                    # Correct action + response + tone
                    return 0.9, "✓ Sent password reset (0.9)"
                else:
                    return -0.5, "✗ Wrong email address (-0.5)"
            else:
                self.wrong_action_count += 1
                return -0.5, f"✗ Wrong action: {action.tool_name} (-0.5)"
        else:
            # Step 2
            if action.tool_name == "close_ticket":
                return 0.3, "✓ Closed ticket (0.3)"
            elif action.tool_name == self.last_action:
                return -0.3, f"✗ Repeated {action.tool_name} (-0.3)"
            else:
                self.wrong_action_count += 1
                return -0.5, f"✗ Wrong action: {action.tool_name} (-0.5)"
    
    def _grade_medium(self, action: Action) -> tuple:
        """Grade medium task (refund request).
        
        Min steps: 2
        - Step 1: request_logs OR reply_to_customer → +0.4
        - Step 2: reply_to_customer with denial → +0.9
        """
        if self.step_count == 1:
            if action.tool_name == "request_logs":
                # Check policy first (good practice)
                return 0.4, "✓ Checked policy"
            elif action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "deny" in content or "cannot" in content or "30" in content:
                    # Direct response with denial
                    return 0.7, "✓ Direct response with denial (0.7)"
                else:
                    return -0.5, "✗ Wrong response (-0.5)"
            elif action.tool_name == "issue_refund":
                # CRITICAL: Cannot refund after 30 days
                self.wrong_action_count += 3  # Auto-fail
                return -0.5, "✗ POLICY VIOLATION: Cannot refund (-0.5)"
            else:
                self.wrong_action_count += 1
                return -0.5, f"✗ {action.tool_name} (-0.5)"
        else:
            # Step 2+
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "deny" in content or "cannot" in content or "30" in content:
                    # Proper denial
                    return 0.9, "✓ Proper denial (0.9)"
                else:
                    return -0.5, "✗ Weak denial (-0.5)"
            elif action.tool_name == "issue_refund":
                self.wrong_action_count += 3
                return -0.5, "✗ POLICY VIOLATION (-0.5)"
            elif action.tool_name == self.last_action:
                return -0.3, f"✗ Repeated action (-0.3)"
            else:
                self.wrong_action_count += 1
                return -0.5, f"✗ {action.tool_name} (-0.5)"
    
    def _grade_hard(self, action: Action) -> tuple:
        """Grade hard task (technical troubleshooting).
        
        Min steps: 3
        Required sequence: request_logs → reply_to_customer (with solution) → close_ticket
        
        - Step 1: request_logs → +0.7
        - Step 2: reply with v2.1 → +0.9
        - Step 3: close_ticket → +0.4
        """
        # Track sequence
        self.hard_task_sequence.append(action.tool_name)
        
        # Validate sequence
        expected = ['request_logs', 'reply_to_customer', 'close_ticket']
        expected_action = expected[min(self.step_count - 1, 2)]
        
        if self.step_count == 1:
            if action.tool_name == "request_logs":
                return 0.7, "✓ Requested logs (0.7)"
            else:
                self.wrong_action_count += 1
                return -0.5, f"✗ Must request logs first (-0.5)"
        
        elif self.step_count == 2:
            if action.tool_name == "reply_to_customer":
                content = str(action.tool_args.get("content", "")).lower()
                if "v2.1" in content or "update client" in content:
                    return 0.9, "✓ Correct diagnosis with v2.1 (0.9)"
                else:
                    self.wrong_action_count += 1
                    return -0.5, "✗ Wrong diagnosis (-0.5)"
            else:
                self.wrong_action_count += 1
                return -0.5, f"✗ Wrong action (need reply_to_customer) (-0.5)"
        
        else:
            # Step 3+
            if action.tool_name == "close_ticket":
                return 0.4, "✓ Closed ticket (0.4)"
            elif action.tool_name == "reply_to_customer":
                return -0.3, "✗ Extra communication (-0.3)"
            elif action.tool_name == self.last_action:
                return -0.3, "✗ Repeated action (-0.3)"
            else:
                return -0.5, f"✗ {action.tool_name} (-0.5)"
    
    def get_final_score(self) -> float:
        """Get final normalized score."""
        return self.calculator.get_score(max_reward=2.5)  # Typical max is ~2.5 over task
