"""Report formatters: turn API data into markdown without LLM.

Use these functions to generate GLPI, Zabbix, Linear and dashboard reports
from the same structures returned by core/tools and core/integrations.
"""

from .glpi import (
    format_glpi_report,
    format_tickets_table,
    format_new_unassigned_report,
    format_pending_old_report,
)
from .zabbix import format_zabbix_report, format_alerts_table
from .linear import format_linear_report, format_issues_table
from .dashboard import format_dashboard_report
from .itil import format_itil_classification_block

__all__ = [
    "format_glpi_report",
    "format_tickets_table",
    "format_new_unassigned_report",
    "format_pending_old_report",
    "format_zabbix_report",
    "format_alerts_table",
    "format_linear_report",
    "format_issues_table",
    "format_dashboard_report",
    "format_itil_classification_block",
]
