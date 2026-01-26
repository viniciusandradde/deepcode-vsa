"""Tests for Agent State and Nodes."""

import pytest

from deepcode_vsa.agent.state import (
    VSAAgentState,
    Methodology,
    TaskCategory,
    Priority,
    create_initial_state,
)
from deepcode_vsa.agent.nodes import classifier, planner, executor, analyzer


class TestAgentState:
    """Tests for VSAAgentState."""
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state(
            user_request="Test request",
            session_id="test-123",
            dry_run=True
        )
        
        assert state["user_request"] == "Test request"
        assert state["session_id"] == "test-123"
        assert state["dry_run"] is True
        assert state["current_step"] == 0
        assert state["plan"] is None
        assert state["should_continue"] is True
        assert state["error"] is None
    
    def test_methodology_enum(self):
        """Test Methodology enum values."""
        assert Methodology.ITIL.value == "itil"
        assert Methodology.GUT.value == "gut"
        assert Methodology.RCA.value == "rca"
        assert Methodology.W5H2.value == "5w2h"
    
    def test_task_category_enum(self):
        """Test TaskCategory enum values."""
        assert TaskCategory.INCIDENT.value == "incident"
        assert TaskCategory.PROBLEM.value == "problem"
        assert TaskCategory.CHANGE.value == "change"
        assert TaskCategory.REQUEST.value == "request"
    
    def test_priority_enum(self):
        """Test Priority enum values."""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


class TestClassifierNode:
    """Tests for Classifier node."""
    
    def test_classify_task_incident(self):
        """Test incident classification."""
        result = classifier.classify_task("servidor está down")
        assert result == TaskCategory.INCIDENT
    
    def test_classify_task_problem(self):
        """Test problem classification."""
        result = classifier.classify_task("recurring issue")
        assert result == TaskCategory.PROBLEM
    
    def test_estimate_gut(self):
        """Test GUT estimation."""
        g, u, t, score = classifier.estimate_gut("production down urgente piorando")
        
        assert g == 5  # Critical = 5
        assert u == 5  # Urgent = 5
        assert t == 5  # Getting worse = 5
        assert score == 125
    
    def test_determine_priority(self):
        """Test priority determination."""
        assert classifier.determine_priority(125) == Priority.CRITICAL
        assert classifier.determine_priority(64) == Priority.HIGH
        assert classifier.determine_priority(30) == Priority.MEDIUM
        assert classifier.determine_priority(10) == Priority.LOW
    
    def test_select_methodology(self):
        """Test methodology selection."""
        assert classifier.select_methodology(TaskCategory.PROBLEM, "") == Methodology.RCA
        assert classifier.select_methodology(TaskCategory.INCIDENT, "priorit ranking") == Methodology.GUT
    
    @pytest.mark.asyncio
    async def test_run_node(self):
        """Test classifier node execution."""
        state = create_initial_state(
            user_request="servidor production down immediately piorando",
            session_id="test",
            dry_run=True
        )
        
        result = await classifier.run(state)
        
        assert result["task_category"] == TaskCategory.INCIDENT
        assert result["priority"] in [Priority.CRITICAL, Priority.HIGH]
        assert result["methodology"] is not None
        assert result["gut_score"] >= 60  # At least HIGH priority
        assert len(result["audit_log"]) == 1


class TestPlannerNode:
    """Tests for Planner node."""
    
    def test_generate_plan_rca(self):
        """Test RCA plan generation."""
        plan = planner.generate_plan(Methodology.RCA, None, "")
        
        assert len(plan) == 5
        assert "5 Porquês" in plan[1]
    
    def test_generate_plan_gut(self):
        """Test GUT plan generation."""
        plan = planner.generate_plan(Methodology.GUT, None, "")
        
        assert len(plan) == 7
        assert "GUT" in plan[4]
    
    def test_generate_plan_itil(self):
        """Test ITIL plan generation."""
        plan = planner.generate_plan(Methodology.ITIL, TaskCategory.INCIDENT, "")
        
        assert len(plan) >= 5
    
    @pytest.mark.asyncio
    async def test_run_node(self):
        """Test planner node execution."""
        state = create_initial_state(
            user_request="test",
            session_id="test",
            dry_run=True
        )
        state["methodology"] = Methodology.RCA
        state["task_category"] = TaskCategory.PROBLEM
        
        result = await planner.run(state)
        
        assert result["plan"] is not None
        assert len(result["plan"]) > 0
        assert result["current_step"] == 0
        assert result["needs_replan"] is False


class TestExecutorNode:
    """Tests for Executor node."""
    
    @pytest.mark.asyncio
    async def test_run_with_steps(self):
        """Test executor with available steps."""
        state = create_initial_state(
            user_request="test",
            session_id="test",
            dry_run=True
        )
        state["plan"] = ["Step 1", "Step 2", "Step 3"]
        state["current_step"] = 0
        
        result = await executor.run(state)
        
        assert result["current_step"] == 1
        assert result["should_continue"] is True
        assert len(result["tool_results"]) == 1
    
    @pytest.mark.asyncio
    async def test_run_all_done(self):
        """Test executor when all steps are done."""
        state = create_initial_state(
            user_request="test",
            session_id="test",
            dry_run=True
        )
        state["plan"] = ["Step 1"]
        state["current_step"] = 1  # Already past last step
        
        result = await executor.run(state)
        
        assert result["should_continue"] is False


class TestAnalyzerNode:
    """Tests for Analyzer node."""
    
    @pytest.mark.asyncio
    async def test_run_not_complete(self):
        """Test analyzer when not complete."""
        state = create_initial_state(
            user_request="test",
            session_id="test",
            dry_run=True
        )
        state["plan"] = ["Step 1", "Step 2", "Step 3"]
        state["current_step"] = 1
        state["tool_results"] = [{"success": True}]
        
        result = await analyzer.run(state)
        
        assert result["should_continue"] is True
        assert result["needs_replan"] is False
    
    @pytest.mark.asyncio
    async def test_run_complete(self):
        """Test analyzer when complete."""
        state = create_initial_state(
            user_request="test",
            session_id="test",
            dry_run=True
        )
        state["plan"] = ["Step 1"]
        state["current_step"] = 1  # All done
        state["methodology"] = Methodology.GUT
        state["tool_results"] = []
        
        result = await analyzer.run(state)
        
        assert result["should_continue"] is False
