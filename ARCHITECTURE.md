# OpenEnv Architecture

## Overview

OpenEnv is a modular reinforcement learning environment designed for training and evaluating agents on support ticket tasks. The architecture follows a standard RL environment pattern with clear separation of concerns.

## Core Components

### 1. Environment (`env/`)

The main environment module manages the interaction loop between agents and tasks.

**Classes:**
- `Environment` - Main environment class
- `Task` - Data model for tasks
- `Agent` - Data model for agents
- `State` - Data model for environment state

**Responsibilities:**
- Manage episode lifecycle (reset, step, done)
- Track step counts and episode metrics
- Interface between agents and tasks
- Coordinate with graders for reward calculation

### 2. Tasks (`tasks/`)

Task implementations organized by difficulty level.

**Architecture:**
- `BaseTask` - Abstract base class defining task interface
- `EasyTask`, `MediumTask`, `HardTask` - Difficulty-specific implementations

**Task Interface:**
- `reset()` - Initialize/reset task state
- `step(action)` - Process action and return new state
- `is_complete()` - Check if task is solved
- `get_state()` - Retrieve current state

### 3. Graders (`graders/`)

Evaluation and reward calculation system.

**Classes:**
- `BaseGrader` - Abstract grader base class
- `SupportGrader` - Specialized grader for support tasks
- `RewardCalculator` - Utility for reward calculations

**Features:**
- Task completion evaluation
- Policy compliance checking
- Forbidden phrase detection
- Reward calculation with penalties

### 4. Agents (`agents/`)

Agent implementations for solving tasks.

**Classes:**
- `BaseAgent` - Abstract base class
- `DummyAgent` - Baseline agent for testing
- `HFAgent` - Hugging Face model-based agent

**Agent Interface:**
- `act(observation)` - Generate action from observation
- `reset()` - Reset agent state
- `get_action_history()` - Retrieve action history

## Data Flow

```
┌─────────────────┐
│   Observation   │
└────────┬────────┘
         │
         v
    ┌────────┐
    │ Agent  │
    └────┬───┘
         │
         v
    ┌────────────┐
    │   Action   │
    └────┬───────┘
         │
         v
┌────────────────────────┐
│   Environment.step()   │
└────┬───────────────────┘
     │
     ├─→ Task.step(action)
     │   ├─→ Process action
     │   └─→ Return new state
     │
     ├─→ Task.is_complete()
     │   └─→ Check completion
     │
     └─→ Grader.grade()
         ├─→ Check policy compliance
         ├─→ Check forbidden phrases
         └─→ Calculate reward

     v
┌──────────────────────┐
│  (obs, r, d, info)   │
└──────────────────────┘
```

## Module Dependencies

```
app.py
  ├── Environment (env/)
  ├── Task classes (tasks/)
  ├── Graders (graders/)
  └── Agents (agents/)

tests/
  ├── tasks/
  ├── graders/
  ├── agents/
  └── env/

scripts/
  ├── baseline.py
  └── run_env.py
```

## Key Design Patterns

### 1. Abstract Base Classes
- All major components use ABC for extensibility
- Clear interfaces for implementing new variants

### 2. Composition
- Environment composes tasks, graders, and agents
- Allows flexible configuration and testing

### 3. State Management
- Explicit state handling in tasks and environment
- Easy to track and debug

### 4. Separation of Concerns
- Tasks handle mechanics
- Graders handle evaluation
- Agents handle decision-making
- Environment coordinates

## Configuration

Configuration is handled at multiple levels:

1. **Settings Module** (`config/settings.py`)
   - Path definitions
   - Default parameters
   - File locations

2. **YAML Config** (`openenv.yaml`)
   - Environment defaults
   - Task settings
   - Agent configurations

3. **Environment Variables** (`.env`)
   - Sensitive credentials
   - Runtime overrides

## Testing Strategy

The test suite is organized by component:

- `test_environment.py` - Environment tests
- `test_graders.py` - Grader tests
- `test_models.py` - Data model tests
- `test_rewards.py` - Reward calculation tests

Tests use fixtures defined in `conftest.py` for consistent test data.

## Extension Points

### Adding a New Agent Type
1. Create new class inheriting from `BaseAgent`
2. Implement `act()` method
3. Register in `agents/__init__.py`
4. Add to `scripts/run_env.py`

### Adding a New Task Difficulty
1. Create task class inheriting from `BaseTask`
2. Implement required methods
3. Add to `tasks/__init__.py`
4. Create corresponding data file

### Adding a New Grader
1. Create class inheriting from `BaseGrader`
2. Implement `grade()` method
3. Register in `graders/__init__.py`

## Performance Considerations

- **Agent.act()** - Called every step; optimize for latency
- **Grader.grade()** - Called every step; cache policy/phrase data
- **Task.step()** - Called every step; keep stateless where possible
- **Environment** - Main loop; minimize overhead

## Future Enhancements

- Multi-agent support
- Curriculum learning
- Advanced reward shaping
- Distributed evaluation
- Web API interface
