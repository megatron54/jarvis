"""Workflow engine for multi-step automations."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


class WorkflowStep:
    """A single step in a workflow."""

    def __init__(self, name: str, action: str, params: dict[str, Any], condition: str | None = None):
        self.name = name
        self.action = action
        self.params = params
        self.condition = condition
        self.result: Any = None
        self.status: str = "pending"


class Workflow:
    """A sequence of steps to execute."""

    def __init__(self, name: str, steps: list[WorkflowStep]):
        self.name = name
        self.steps = steps
        self.context: dict[str, Any] = {}

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        """Create workflow from dictionary (YAML/JSON config)."""
        steps = []
        for step_data in data.get("steps", []):
            steps.append(WorkflowStep(
                name=step_data["name"],
                action=step_data["action"],
                params=step_data.get("params", {}),
                condition=step_data.get("condition"),
            ))
        return cls(name=data["name"], steps=steps)


class WorkflowEngine:
    """Execute workflows with step-by-step control."""

    def __init__(self, tool_registry: Any):
        self._tools = tool_registry
        self._workflows: dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.name] = workflow

    async def execute(self, workflow_name: str, context: dict | None = None) -> dict:
        """Execute a workflow by name."""
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            return {"error": f"Workflow '{workflow_name}' not found"}

        workflow.context = context or {}
        results = []

        for step in workflow.steps:
            logger.info("Executing workflow step", workflow=workflow_name, step=step.name)

            # Check condition
            if step.condition and not self._evaluate_condition(step.condition, workflow.context):
                step.status = "skipped"
                continue

            # Resolve params with context variables
            resolved_params = self._resolve_params(step.params, workflow.context)

            # Execute
            try:
                result = await self._tools.execute(step.action, resolved_params)
                step.result = result
                step.status = "completed"
                workflow.context[f"step_{step.name}"] = result
                results.append({"step": step.name, "status": "completed", "result": result})
            except Exception as e:
                step.status = "failed"
                results.append({"step": step.name, "status": "failed", "error": str(e)})
                break  # Stop on failure

        return {"workflow": workflow_name, "results": results}

    def _resolve_params(self, params: dict, context: dict) -> dict:
        """Replace {{var}} references in params with context values."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and "{{" in value:
                for ctx_key, ctx_val in context.items():
                    value = value.replace(f"{{{{{ctx_key}}}}}", str(ctx_val))
            resolved[key] = value
        return resolved

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """Simple condition evaluation."""
        # Basic truthy check on context value
        parts = condition.split("==")
        if len(parts) == 2:
            key = parts[0].strip()
            expected = parts[1].strip().strip("'\"")
            return str(context.get(key, "")) == expected
        return bool(context.get(condition.strip()))
