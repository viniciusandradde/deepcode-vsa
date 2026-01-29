"""Dashboard report: GLPI + Zabbix combined markdown."""

from .glpi import format_glpi_report
from .zabbix import format_zabbix_report
from .linear import format_linear_report


def format_dashboard_report(
    glpi_data: dict | None = None,
    zabbix_data: dict | None = None,
    linear_data: dict | None = None,
) -> str:
    """Gera relatório dashboard combinando GLPI, Zabbix e opcionalmente Linear."""
    sections = []

    sections.append("## Dashboard - Visão geral\n")

    if glpi_data is not None:
        sections.append(format_glpi_report(glpi_data))

    if zabbix_data is not None:
        sections.append(format_zabbix_report(zabbix_data))

    if linear_data is not None:
        sections.append(format_linear_report(linear_data))

    if not sections or sections == ["## Dashboard - Visão geral\n"]:
        return "**Nenhum dado disponível.** Configure GLPI e/ou Zabbix para ver o dashboard."

    return "\n\n---\n\n".join(sections)
