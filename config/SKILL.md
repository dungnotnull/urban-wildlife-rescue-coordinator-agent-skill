---
name: skill-registry
description: Comprehensive skill registry documentation for urban-wildlife-rescue-coordinator — defines how skills are registered, resolved, executed, and validated with complete JSON schemas for input/output.
---

# Skill Registry — Urban Wildlife Rescue Coordinator v1.0

## Overview

The **Skill Registry** is the central component that manages all domain skills in the urban-wildlife-rescue-coordinator system. It provides a unified interface for skill registration, resolution, execution, validation, and lifecycle management.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Registry                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Skill Registration Layer                   │    │
│  │  • Dynamic skill loading from /skills directory      │    │
│  │  • Frontmatter parsing & validation                 │    │
│  │  • Dependency resolution                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Skill Resolution Layer                     │    │
│  │  • Pattern matching on user queries                 │    │
│  │  • Skill priority scoring                           │    │
│  │  • Multi-skill orchestration                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Skill Execution Layer                      │    │
│  │  • Pre-execution hooks                               │    │
│  │  • Input validation                                 │    │
│  │  • Skill invocation                                  │    │
│  │  • Output validation                                 │    │
│  │  • Post-execution hooks                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Quality Gate Layer                         │    │
│  │  • Universal gates (U1-U6)                           │    │
│  │  • Domain gates (G1-G4)                             │    │
│  │  • Auto-fix & retry logic                            │    │
│  │  • Graceful degradation                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Skill File Format

Every skill file MUST follow this format:

```markdown
---
name: {skill-identifier}
description: {one-line summary that describes when to trigger this skill}
---

## Role & Persona
{Who the skill embodies and its expertise}

## Workflow (Harness Flow)
{Step-by-step execution protocol}

## Tools
{List of tools the skill can invoke}

## Output Format
{Expected output structure and template}

## Quality Gates
{Specific quality checks for this skill}
```

### Required Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill identifier (kebab-case) |
| `description` | string | Yes | One-line trigger description (make it "pushy" to improve triggering) |

### Optional Frontmatter Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | "1.0.0" | Skill version |
| `priority` | number | 50 | Execution priority (0-100, higher first) |
| `enabled` | boolean | true | Whether skill is available |
| `dependencies` | list | [] | Other skills this skill requires |

## Input/Output JSON Schemas

### Standard Skill Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SkillInput",
  "type": "object",
  "properties": {
    "skill_name": {
      "type": "string",
      "description": "Name of the skill to execute"
    },
    "inputs": {
      "type": "object",
      "description": "Input parameters for the skill",
      "additionalProperties": true
    },
    "context": {
      "type": "object",
      "description": "Execution context with metadata",
      "properties": {
        "language": {"type": "string", "enum": ["en", "vi"]},
        "user_id": {"type": "string"},
        "session_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"}
      }
    },
    "options": {
      "type": "object",
      "description": "Execution options",
      "properties": {
        "dry_run": {"type": "boolean"},
        "debug": {"type": "boolean"},
        "timeout_ms": {"type": "number"}
      }
    }
  },
  "required": ["skill_name"]
}
```

### Standard Skill Output Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SkillOutput",
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether execution succeeded"
    },
    "outputs": {
      "type": "object",
      "description": "Skill execution outputs",
      "additionalProperties": true
    },
    "errors": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Error messages if any"
    },
    "metadata": {
      "type": "object",
      "description": "Execution metadata",
      "properties": {
        "execution_time_ms": {"type": "number"},
        "tokens_used": {"type": "number"},
        "gates_checked": {"type": "array", "items": {"type": "string"}},
        "degradation_level": {"type": "number"}
      }
    },
    "quality_checks": {
      "type": "object",
      "description": "Quality gate results",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "passed": {"type": "boolean"},
          "message": {"type": "string"},
          "auto_fix_applied": {"type": "boolean"}
        }
      }
    }
  },
  "required": ["success"]
}
```

## Skill Registration

### Automatic Registration

Skills are automatically registered from the `/skills` directory at startup:

```python
from config import get_hooks, HookEvent, HookContext

# Register all skills from directory
registry = SkillRegistry()
registry.register_from_directory("/path/to/skills")

# Emit registration event
hooks = get_hooks()
hooks.emit(HookEvent.SKILL_REGISTERED, HookContext(
    event=HookEvent.SKILL_REGISTERED,
    metadata={"skill_count": len(registry.all_skills())}
))
```

### Manual Registration

```python
from skills import CustomSkill

registry = SkillRegistry()
registry.register(CustomSkill(
    name="custom-skill",
    description="Custom domain skill",
    priority=75
))
```

## Skill Resolution

### Pattern Matching

Skills are resolved based on user query patterns:

```python
query = "Analyze urban wildlife rescue case for injured hawk"

resolved_skills = registry.resolve(
    query=query,
    context={"language": "en", "domain": "wildlife_rescue"}
)

# Returns: [urban-wildlife-rescue-coordinator]
```

### Resolution Algorithm

1. **Keyword Extraction**: Extract domain keywords from query
2. **Skill Scoring**: Score each skill based on:
   - Description keyword match (40%)
   - Name similarity (30%)
   - Priority setting (20%)
   - Historical success rate (10%)
3. **Threshold Filtering**: Filter skills below minimum score (0.3)
4. **Dependency Check**: Verify all dependencies are available
5. **Multi-Skill Selection**: If multiple skills qualify, select top N

### Skill Priority

Skills are executed in priority order:

| Priority Range | Description | Example Skills |
|----------------|-------------|----------------|
| 90-100 | Critical system skills | error-handler, safety-check |
| 70-89 | High-priority domain skills | core-analysis, advisor |
| 50-69 | Standard skills | evidence-collector |
| 30-49 | Auxiliary skills | knowledge-updater |
| 0-29 | Experimental skills | experimental-feature |

## Skill Execution

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Flow                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. PRE_EXECUTION Hook                                      │
│     • Validate inputs                                       │
│     • Check dependencies                                    │
│     • Initialize context                                    │
│                          │                                  │
│  2. Skill Input Validation                                │
│     • JSON schema validation                                │
│     • Type checking                                         │
│     • Required field verification                           │
│                          │                                  │
│  3. Skill Invocation                                       │
│     • Load skill file                                       │
│     • Parse workflow instructions                           │
│     • Execute skill logic                                   │
│                          │                                  │
│  4. Skill Output Validation                                │
│     • JSON schema validation                                │
│     • Quality gate checks                                   │
│     • Auto-fix application                                  │
│                          │                                  │
│  5. POST_EXECUTION Hook                                    │
│     • Log execution metrics                                 │
│     • Update knowledge base                                │
│     • Emit completion event                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Execution Example

```python
from config import get_hooks, HookEvent, HookContext

# Create execution context
context = HookContext(
    event=HookEvent.PRE_EXECUTION,
    config=get_config(),
    metadata={"skill": "urban-wildlife-rescue-coordinator"}
)

# Pre-execution hook
pre_result = hooks.emit(HookEvent.PRE_EXECUTION, context)
if pre_result.should_abort:
    return {"success": False, "errors": pre_result.errors}

# Execute skill
try:
    result = execute_skill(
        skill_name="urban-wildlife-rescue-coordinator",
        inputs={"query": query, "language": "en"}
    )

    # Post-execution hook
    post_context = context.with_outputs(result)
    hooks.emit(HookEvent.POST_EXECUTION, post_context)

    return result
except Exception as e:
    # Error hook
    error_context = context.with_error(e)
    hooks.emit(HookEvent.ON_ERROR, error_context)
    raise
```

## Quality Gates

### Universal Gates (U1-U6)

Applied to ALL skills:

| Gate | Check | Auto-Fix | Retry Limit |
|------|-------|----------|-------------|
| U1 | ≥3 sources cited, ≥1 academic/authoritative | Fetch from KB | 2 |
| U2 | Disclosure/limitations before recommendation | Prepend disclosure | 2 |
| U3 | Evidence hierarchy stated per source | Annotate tiers | 2 |
| U4 | Language matches user preference | Translate output | 2 |
| U5 | Output uses declared template | Reformat to template | 2 |
| U6 | Every claim traceable to source or flagged | Mark claims | 2 |

### Domain Gates (G1-G4)

Applied to specific domain skills:

| Gate | Domain | Check | Auto-Fix |
|------|--------|-------|----------|
| G1 | Wildlife Rescue | Species ID & triage performed | Identify & triage |
| G2 | Wildlife Rescue | Safe capture/handling with zoonosis | Add capture/zoonosis |
| G3 | Wildlife Rescue | Rehab/release or coexistence decision | Decide rehab/coexistence |
| G4 | Wildlife Rescue | Coordination & permits considered | Consider coordination |

### Gate Enforcement

```python
from config.gates import GateChecker

checker = GateChecker()

# Check all gates
result = checker.check_all(
    output=skill_output,
    gates=["U1", "U2", "U3", "U4", "U5", "U6", "G1", "G2", "G3", "G4"]
)

# Apply auto-fix for failed gates
for gate_result in result.failed_gates:
    if gate_result.auto_fix_available:
        fixed_output = checker.apply_auto_fix(
            output=skill_output,
            gate=gate_result.gate_name
        )
```

## Skill Lifecycle

### Lifecycle States

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ REGISTER │───▶│  LOADED  │───▶│ EXECUTING│───▶│ COMPLETE │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                   │                                │
                   │                                ▼
                   │                          ┌──────────┐
                   │                          │  FAILED  │
                   │                          └──────────┘
                   │                                │
                   ▼                                ▼
              ┌──────────┐                    ┌──────────┐
              │ DISABLED │◀───────────────────│ ERROR    │
              └──────────┘                    └──────────┘
```

### State Transitions

| From State | To State | Trigger |
|------------|----------|---------|
| REGISTERED | LOADED | Skill file parsed successfully |
| LOADED | EXECUTING | Execution initiated |
| EXECUTING | COMPLETE | All quality gates passed |
| EXECUTING | FAILED | Quality gate failure (no auto-fix) |
| EXECUTING | ERROR | Exception during execution |
| ANY | DISABLED | Manual disable or dependency failure |
| FAILED | LOADED | Auto-fix applied, retry allowed |
| ERROR | LOADED | Error resolved, retry allowed |

## Skill Metadata

### Metadata Schema

```json
{
  "name": "urban-wildlife-rescue-coordinator",
  "version": "1.0.0",
  "description": "Urban Wildlife Rescue Coordination Advisor",
  "author": "972026 Skill Library",
  "created_at": "2026-07-13T00:00:00Z",
  "updated_at": "2026-07-27T00:00:00Z",
  "execution_stats": {
    "total_executions": 150,
    "success_rate": 0.95,
    "avg_execution_time_ms": 8500,
    "avg_tokens_used": 12000
  },
  "quality_metrics": {
    "gate_pass_rate": 0.98,
    "auto_fix_success_rate": 0.85,
    "user_satisfaction_score": 4.7
  },
  "dependencies": [
    "sub-gather-requirements",
    "sub-evidence-collector",
    "sub-core-analysis",
    "sub-knowledge-updater",
    "sub-advisor"
  ]
}
```

## Error Handling

### Error Categories

| Category | Description | Recovery Action |
|----------|-------------|-----------------|
| VALIDATION_ERROR | Input validation failed | Return error message |
| DEPENDENCY_ERROR | Required skill missing | Degrade gracefully |
| EXECUTION_ERROR | Skill execution failed | Retry with fallback |
| GATE_FAILURE | Quality gate failed | Apply auto-fix |
| TIMEOUT_ERROR | Execution exceeded limit | Abort and report |
| RESOURCE_ERROR | External resource unavailable | Use cached data |

### Error Recovery

```python
from config import get_hooks, HookEvent, HookContext

def execute_skill_with_recovery(skill_name: str, inputs: dict):
    try:
        return execute_skill(skill_name, inputs)
    except ValidationError as e:
        # Return specific error message
        return {"success": False, "errors": [str(e)]}
    except DependencyError as e:
        # Degrade gracefully
        hooks.emit(HookEvent.ON_DEGRADATION, HookContext(
            event=HookEvent.ON_DEGRADATION,
            metadata={"missing_dependency": str(e)}
        ))
        return execute_skill_fallback(skill_name, inputs)
    except ExecutionError as e:
        # Retry with exponential backoff
        return retry_with_backoff(skill_name, inputs, max_retries=3)
```

## Monitoring & Observability

### Execution Metrics

Track these metrics for all skill executions:

- **Latency**: Execution time in milliseconds
- **Success Rate**: Percentage of successful executions
- **Token Usage**: Total tokens consumed
- **Gate Pass Rate**: Percentage of gates passed
- **Auto-Fix Rate**: Percentage of gates fixed automatically
- **Degradation Events**: Number of times graceful degradation was triggered

### Logging

```python
import logging

logger = logging.getLogger("skill_registry")

# Log execution start
logger.info("Starting skill execution", extra={
    "skill_name": skill_name,
    "inputs": inputs,
    "timestamp": datetime.now(timezone.utc).isoformat()
})

# Log execution result
logger.info("Skill execution completed", extra={
    "skill_name": skill_name,
    "success": result["success"],
    "execution_time_ms": result["metadata"]["execution_time_ms"],
    "tokens_used": result["metadata"]["tokens_used"]
})
```

## Best Practices

### Skill Design

1. **Keep skills focused**: Each skill should have a single, clear purpose
2. **Use descriptive names**: Make skill names self-documenting
3. **Write "pushy" descriptions**: Improve triggering by making descriptions more explicit
4. **Define clear inputs/outputs**: Use JSON schemas for validation
5. **Include quality gates**: Ensure output quality with specific checks

### Skill Registration

1. **Use automatic registration**: Leverage directory scanning for consistency
2. **Set appropriate priorities**: Higher priority for critical skills
3. **Declare dependencies**: Explicitly list required skills
4. **Version your skills**: Use semantic versioning

### Skill Execution

1. **Always validate inputs**: Check inputs before processing
2. **Handle errors gracefully**: Never let exceptions propagate unhandled
3. **Log execution metrics**: Track performance and success rates
4. **Use hooks for cross-cutting concerns**: Pre/post execution logic in hooks

### Quality Gates

1. **Define specific checks**: Gates should be objectively verifiable
2. **Provide auto-fix**: Where possible, automatically fix gate failures
3. **Limit retry attempts**: Avoid infinite retry loops
4. **Document degradation behavior**: Clearly state what happens when gates fail

---

## Appendix: Complete Skill Registry API

### SkillRegistry Class

```python
class SkillRegistry:
    """Central registry for all domain skills."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the skill registry."""

    def register(self, skill: Skill) -> None:
        """Register a skill with the registry."""

    def register_from_directory(self, directory: Path) -> int:
        """Register all skills from a directory."""

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill by name."""

    def resolve(self, query: str, context: Dict[str, Any]) -> List[Skill]:
        """Resolve skills based on query and context."""

    def execute(self, skill_name: str, inputs: Dict[str, Any]) -> SkillOutput:
        """Execute a skill with inputs."""

    def all_skills(self) -> Dict[str, Skill]:
        """Get all registered skills."""

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a specific skill by name."""

    def update_metadata(self, skill_name: str, metadata: Dict[str, Any]) -> None:
        """Update skill metadata."""

    def get_execution_stats(self, skill_name: str) -> ExecutionStats:
        """Get execution statistics for a skill."""
```

### HookRegistry Integration

```python
from config import get_hooks, HookEvent, HookContext

# Emit skill registration event
hooks = get_hooks()
hooks.emit(HookEvent.SKILL_REGISTERED, HookContext(
    event=HookEvent.SKILL_REGISTERED,
    metadata={"skill_name": skill.name, "skill_count": len(registry.all_skills())}
))

# Emit skill execution event
hooks.emit(HookEvent.PRE_SKILL_INVOKE, HookContext(
    event=HookEvent.PRE_SKILL_INVOKE,
    skill_name=skill_name,
    inputs=inputs
))

hooks.emit(HookEvent.POST_SKILL_INVOKE, HookContext(
    event=HookEvent.POST_SKILL_INVOKE,
    skill_name=skill_name,
    outputs=result
))
```

---

**Version**: 1.0.0
**Last Updated**: 2026-07-27
**Maintained By**: 972026 Skill Library
