"""Medium task implementations."""
from typing import Any, Dict
from .base_task import BaseTask


class MediumTask(BaseTask):
    """Medium difficulty tasks for OpenEnv."""
    
    def __init__(self, task_id: str, title: str, description: str, initial_data: Dict[str, Any]):
        """
        Initialize a medium task.
        
        Args:
            task_id: Unique identifier for the task
            title: Task title
            description: Task description
            initial_data: Initial task data
        """
        super().__init__(task_id, title, description)
        self.initial_data = initial_data
        self.state = None
    
    def reset(self) -> Dict[str, Any]:
        """Reset the task to initial state."""
        self.state = self.initial_data.copy()
        self.completed = False
        return self.state
    
    def step(self, action: str) -> Dict[str, Any]:
        """
        Execute one step of the task.
        
        Args:
            action: The action to execute
            
        Returns:
            Updated state
        """
        if self.state is None:
            self.reset()
        
        # Process action with more complex logic
        self.state['last_action'] = action
        self.state['step_count'] = self.state.get('step_count', 0) + 1
        
        return self.state
    
    def is_complete(self) -> bool:
        """Check if the task has been completed successfully."""
        return self.completed
