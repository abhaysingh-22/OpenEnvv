"""Reward calculation utilities with sophisticated reward shaping."""
from typing import Dict, Any, List


class RewardCalculator:
    """
    Calculate rewards based on various metrics.
    
    Reward Components:
    - Routing accuracy: ±0.4
    - Response quality: 0 → +0.3
    - Tone quality: 0 → +0.2
    - Efficiency penalty: -0.05 per step
    
    Sequence Penalties (Hard Tasks):
    - Wrong sequence at step 1: -0.5
    - Wrong sequence at step 2: -0.4
    - Wrong sequence at step 3+: -0.3
    """
    
    def __init__(self, efficiency_penalty: float = 0.05):
        """
        Initialize reward calculator.
        
        Args:
            efficiency_penalty: Penalty per step taken
        """
        self.efficiency_penalty = efficiency_penalty
        self.action_history: List[Dict[str, Any]] = []
        # Sequence violation penalties for hard tasks
        self.sequence_penalties = {
            'step_1': -0.5,  # Must request logs first
            'step_2': -0.4,  # Must analyze after logs
            'step_3_plus': -0.3  # Must respond with solution
        }
    
    def calculate_step_reward(self, 
                            routing_score: float = 0.0,
                            response_quality: float = 0.0,
                            tone_quality: float = 0.0,
                            step_number: int = 1) -> float:
        """
        Calculate cumulative reward for a single step.
        
        Args:
            routing_score: Routing accuracy (-0.4 to +0.4)
            response_quality: Response quality (0 to +0.3)
            tone_quality: Tone quality (0 to +0.2)
            step_number: Current step number for penalty calculation
            
        Returns:
            Step reward value (typically 0.0 to 0.9)
        """
        # Clamp components
        routing = max(-0.4, min(0.4, routing_score))
        response = max(0.0, min(0.3, response_quality))
        tone = max(0.0, min(0.2, tone_quality))
        
        # Efficiency penalty (increases with steps)
        penalty = self.efficiency_penalty * (step_number - 1)
        
        # Total step reward
        step_reward = routing + response + tone - penalty
        return max(0.0, step_reward)
    
    def calculate_component_rewards(self, 
                                    routing_score: float = 0.0,
                                    response_quality: float = 0.0,
                                    tone_quality: float = 0.0,
                                    step_number: int = 1) -> Dict[str, float]:
        """
        Calculate and return individual component rewards.
        Useful for debugging and detailed reward tracking.
        
        Args:
            routing_score: Routing accuracy (-0.4 to +0.4)
            response_quality: Response quality (0 to +0.3)
            tone_quality: Tone quality (0 to +0.2)
            step_number: Current step number for penalty calculation
            
        Returns:
            Dictionary with routing, response, tone, efficiency_penalty, and total
        """
        # Clamp components
        routing = max(-0.4, min(0.4, routing_score))
        response = max(0.0, min(0.3, response_quality))
        tone = max(0.0, min(0.2, tone_quality))
        
        # Efficiency penalty
        efficiency = self.efficiency_penalty * (step_number - 1)
        
        # Total
        total = routing + response + tone - efficiency
        total = max(0.0, total)
        
        return {
            'routing': routing,
            'response_quality': response,
            'tone_quality': tone,
            'efficiency_penalty': efficiency,
            'total': total
        }
    
    def apply_sequence_penalty(self, is_sequence_violation: bool, step_number: int) -> float:
        """
        Apply strict sequence violation penalty for hard tasks.
        
        Args:
            is_sequence_violation: Whether action violates sequence requirement
            step_number: Current step number (1-indexed)
            
        Returns:
            Penalty value (negative or 0)
        """
        if not is_sequence_violation:
            return 0.0
        
        if step_number == 1:
            return self.sequence_penalties['step_1']
        elif step_number == 2:
            return self.sequence_penalties['step_2']
        else:
            return self.sequence_penalties['step_3_plus']
    
    def calculate_completion_bonus(self, steps_taken: int, min_steps: int) -> float:
        """
        Calculate bonus for completing task efficiently.
        
        Args:
            steps_taken: Number of steps taken
            min_steps: Minimum steps required for task
            
        Returns:
            Bonus value (0 to 0.3)
        """
        if steps_taken <= min_steps:
            return 0.2
        elif steps_taken == min_steps + 1:
            return 0.1
        else:
            return 0.0
    
    def calculate_partial_reward(self, progress: float) -> float:
        """
        Calculate reward for partial task completion.
        
        Args:
            progress: Progress percentage (0-1)
            
        Returns:
            Reward value
        """
        return progress * 0.5  # Max partial is 0.5
    
    def calculate_penalty(self, error_type: str) -> float:
        """
        Calculate penalty for errors.
        
        Penalties are consistent across all tasks:
        - invalid_action: 0.15 (wrong tool used)
        - policy_violation: 0.3 (refund after 30 days, etc.)
        - forbidden_phrase: 0.2 (violated company policy)
        - wrong_routing: 0.4 (completely wrong direction)
        - bad_tone: 0.15 (unprofessional communication)
        - weak_response: 0.1 (insufficient or unclear response)
        - sequence_violation: See apply_sequence_penalty()
        
        Args:
            error_type: Type of error
            
        Returns:
            Penalty value (0 to -0.4)
        """
        penalties = {
            'invalid_action': -0.15,
            'policy_violation': -0.3,
            'forbidden_phrase': -0.2,
            'wrong_routing': -0.4,
            'bad_tone': -0.15,
            'weak_response': -0.1,
            'failure_condition': -0.5  # Task cannot be completed
        }
        return penalties.get(error_type, 0.0)
    
    def apply_failure_condition(self, failure_reason: str) -> float:
        """
        Apply penalty when task reaches failure condition.
        Task cannot be completed when special conditions are violated.
        
        Examples:
        - Medium task: Issuing refund after 30 days
        - Hard task: Providing wrong solution twice
        - Easy task: Closing ticket without verification
        
        Args:
            failure_reason: Description of failure condition
            
        Returns:
            Failure penalty (typically -0.5)
        """
        return self.calculate_penalty('failure_condition')
    
    def reset_history(self) -> None:
        """Reset action history for a new episode."""
        self.action_history = []
    
    def record_action(self, action_dict: Dict[str, Any]) -> None:
        """Record an action for tracking."""
        self.action_history.append(action_dict)
