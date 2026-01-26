"""Tests for ITIL, GUT, RCA, 5W2H methodologies."""

import pytest

from deepcode_vsa.methodologies.analysis_5w2h import Analysis5W2H, create_5w2h
from deepcode_vsa.methodologies.gut import GUTScore, Priority, calculate_priority, estimate_gut
from deepcode_vsa.methodologies.itil import TaskCategory, classify_task, get_sla_hours
from deepcode_vsa.methodologies.rca import create_rca, format_rca_report


class TestITILClassification:
    """Tests for ITIL task classification."""

    def test_classify_incident(self):
        """Test incident detection."""
        assert classify_task("servidor está down") == TaskCategory.INCIDENT
        assert classify_task("sistema não funciona") == TaskCategory.INCIDENT
        assert classify_task("application error 500") == TaskCategory.INCIDENT
        assert classify_task("serviço lento demais") == TaskCategory.INCIDENT

    def test_classify_problem(self):
        """Test problem detection."""
        assert classify_task("problema recorrente de conexão") == TaskCategory.PROBLEM
        assert classify_task("investigar causa raiz") == TaskCategory.PROBLEM
        # Note: "falha" matches INCIDENT before PROBLEM due to pattern order

    def test_classify_change(self):
        """Test change detection."""
        assert classify_task("migrar banco para novo servidor") == TaskCategory.CHANGE
        assert classify_task("upgrade do sistema operacional") == TaskCategory.CHANGE
        assert classify_task("deploy nova versão") == TaskCategory.CHANGE

    def test_classify_request(self):
        """Test request detection."""
        assert classify_task("criar usuário novo") == TaskCategory.REQUEST
        assert classify_task("resetar senha do João") == TaskCategory.REQUEST
        assert classify_task("liberar acesso ao sistema") == TaskCategory.REQUEST

    def test_classify_default(self):
        """Test default classification."""
        assert classify_task("alguma coisa qualquer") == TaskCategory.REQUEST

    def test_get_sla_hours(self):
        """Test SLA hours mapping."""
        assert get_sla_hours(TaskCategory.INCIDENT) == 4
        assert get_sla_hours(TaskCategory.PROBLEM) == 48
        assert get_sla_hours(TaskCategory.CHANGE) == 72
        assert get_sla_hours(TaskCategory.REQUEST) == 24


class TestGUTMatrix:
    """Tests for GUT Matrix prioritization."""

    def test_gut_score_calculation(self):
        """Test GUT score calculation."""
        gut = GUTScore(gravidade=5, urgencia=5, tendencia=5)
        assert gut.score == 125
        assert gut.priority == Priority.CRITICAL

    def test_gut_score_high(self):
        """Test high priority score."""
        gut = GUTScore(gravidade=4, urgencia=4, tendencia=4)
        assert gut.score == 64
        assert gut.priority == Priority.HIGH

    def test_gut_score_medium(self):
        """Test medium priority score."""
        gut = GUTScore(gravidade=3, urgencia=3, tendencia=3)
        assert gut.score == 27  # < 30
        assert gut.priority == Priority.LOW  # Actually low because < 30

    def test_gut_score_validation(self):
        """Test GUT score validation."""
        with pytest.raises(ValueError):
            GUTScore(gravidade=0, urgencia=3, tendencia=3)

        with pytest.raises(ValueError):
            GUTScore(gravidade=6, urgencia=3, tendencia=3)

    def test_estimate_gut_critical(self):
        """Test GUT estimation for critical issues."""
        gut = estimate_gut("production down immediately urgente piorando")
        assert gut.gravidade == 5
        assert gut.urgencia == 5
        assert gut.tendencia == 5
        assert gut.priority == Priority.CRITICAL

    def test_estimate_gut_low(self):
        """Test GUT estimation for low priority."""
        gut = estimate_gut("enhancement nice to have sem pressa stable")
        assert gut.gravidade == 1
        assert gut.urgencia == 1
        assert gut.tendencia == 3  # Default if not found

    def test_calculate_priority(self):
        """Test priority calculation from score."""
        assert calculate_priority(125) == Priority.CRITICAL
        assert calculate_priority(100) == Priority.CRITICAL
        assert calculate_priority(60) == Priority.HIGH
        assert calculate_priority(30) == Priority.MEDIUM
        assert calculate_priority(29) == Priority.LOW


class TestRCA:
    """Tests for Root Cause Analysis."""

    def test_create_rca(self):
        """Test RCA creation."""
        rca = create_rca("Server keeps crashing")
        assert rca.problem_statement == "Server keeps crashing"
        assert len(rca.whys) == 0
        assert rca.root_cause is None

    def test_add_why(self):
        """Test adding Whys to RCA."""
        rca = create_rca("Memory leak")

        rca.add_why("Why is there a memory leak?", "Objects not being garbage collected")
        rca.add_why("Why are objects not collected?", "Circular references")
        rca.add_why("Why are there circular references?", "Event listeners not removed")

        assert len(rca.whys) == 3
        assert rca.whys[0].level == 1
        assert rca.whys[2].level == 3

    def test_rca_completion(self):
        """Test RCA completion check."""
        rca = create_rca("Issue")
        assert not rca.is_complete

        rca.add_why("Q1", "A1")
        rca.add_why("Q2", "A2")
        rca.add_why("Q3", "A3")
        assert not rca.is_complete  # Still no root cause

        rca.set_root_cause("Missing cleanup in event handler")
        assert rca.is_complete

    def test_format_rca_report(self):
        """Test RCA report formatting."""
        rca = create_rca("Test problem")
        rca.add_why("Why?", "Because")
        rca.set_root_cause("The root cause")

        report = format_rca_report(rca)

        assert "# Root Cause Analysis Report" in report
        assert "Test problem" in report
        assert "Why?" in report
        assert "The root cause" in report


class TestAnalysis5W2H:
    """Tests for 5W2H Analysis."""

    def test_create_5w2h(self):
        """Test 5W2H creation."""
        analysis = create_5w2h("Deploy new feature")
        assert analysis.title == "Deploy new feature"
        assert not analysis.is_complete

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        analysis = Analysis5W2H(title="Test")
        assert analysis.completion_percentage == 0.0

        analysis.what = "Deploy feature X"
        assert analysis.completion_percentage == pytest.approx(14.28, rel=0.1)

        analysis.why = "Business requirement"
        analysis.where = "Production server"
        analysis.when = "Next week"
        analysis.who = "DevOps team"
        analysis.how = "Blue-green deployment"
        analysis.how_much = "$500"

        assert analysis.is_complete
        assert analysis.completion_percentage == 100.0

    def test_5w2h_partial(self):
        """Test partial 5W2H."""
        analysis = Analysis5W2H(
            title="Test",
            what="Something",
            why="Reason",
            who="Someone"
        )
        assert not analysis.is_complete
        assert analysis.completion_percentage == pytest.approx(42.85, rel=0.1)
