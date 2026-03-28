# OpenEnv Improvements - Updated Requirements

## 🎯 Hard Task Sequence Dependency

Hard tasks **MUST require**:
- ✓ **Correct sequence** - Actions must follow valid workflow
- ✓ **Correct timing** - Actions must happen in right order
- ✓ **Correct decision** - Actions must make logical sense

### Strict Flow Pattern Example

Implement state-based penalties for sequence violations:

```python
# Hard task grading logic
if not self.logs_requested:
    if action.type != "request_logs":
        penalty = -0.5  # Must request logs first!

elif not self.diagnosed:
    if action.type != "analyze_logs":
        penalty = -0.4  # Must analyze after logs

elif not self.responded:
    if action.type != "reply_to_customer":
        penalty = -0.3  # Must respond with solution
```

---

## 📋 Implementation Roadmap

### Step 1: Fix Hard Task Sequence Dependency
- [ ] Track workflow state in grader
- [ ] Enforce strict action sequencing
- [ ] Apply penalties for out-of-order actions

### Step 2: Break Medium Reward into Components
- [ ] Separate routing, response quality, tone components
- [ ] Calculate component rewards independently
- [ ] Combine for final step reward

### Step 3: Simplify Scoring System
- [ ] Remove confusion in reward calculation
- [ ] Use consistent penalties across tasks
- [ ] Clear documentation of scoring rules

### Step 4: Add Failure Conditions
- [ ] Define when task cannot be completed
- [ ] Implement failure detection
- [ ] Set minimum score thresholds

### Step 5: Test with Different Agents
- [ ] Test with random agent
- [ ] Test with imperfect agent
- [ ] Validate score differentiation

---

## 📊 Expected Baseline Performance

After implementing all improvements, your system should produce:

| Task | Perfect Agent | Imperfect Agent | Random Agent |
|------|:---:|:---:|:---:|
| **Easy** | ~0.85 | ~0.6 | ~0.2 |
| **Medium** | ~0.75 | ~0.5 | ~0.2 |
| **Hard** | ~0.6–0.7 | ~0.3–0.5 | ~0.0–0.2 |

### Key Metrics
- **Perfect Agent**: Follows correct sequence, good tone, efficient execution
- **Imperfect Agent**: Mixed quality, occasional wrong actions, some efficiency issues
- **Random Agent**: No coherent strategy, low scores across all tasks

---

## ✅ Validation Checklist

- [ ] Hard task penalizes wrong sequence order
- [ ] Medium task breaks rewards into components
- [ ] Scoring is deterministic and reproducible
- [ ] Perfect agent scores 0.85+ average
- [ ] Imperfect agent scores 0.3-0.6 average
- [ ] Random agent scores 0.0-0.2 average
- [ ] No task scores 1.0 instantly