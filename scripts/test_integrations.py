#!/usr/bin/env python3
"""Script para testar integrações GLPI, Zabbix e Linear.

Uso:
    python scripts/test_integrations.py
    python scripts/test_integrations.py --glpi
    python scripts/test_integrations.py --zabbix
    python scripts/test_integrations.py --linear
    python scripts/test_integrations.py --all
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_settings
from core.integrations.glpi_client import GLPIClient
from core.integrations.zabbix_client import ZabbixClient
from core.integrations.linear_client import LinearClient


async def test_glpi():
    """Test GLPI integration."""
    print("\n" + "="*60)
    print("🔍 Testando GLPI Integration")
    print("="*60)

    settings = get_settings()

    if not settings.glpi.enabled:
        print("❌ GLPI não está habilitado")
        return False

    print(f"📡 Base URL: {settings.glpi.base_url}")
    print(f"🔑 App Token: {settings.glpi.app_token[:10]}...")

    client = GLPIClient(settings.glpi)

    try:
        # Test session init
        print("\n1️⃣ Inicializando sessão...")
        result = await client.init_session()

        if not result.success:
            print(f"❌ Falha na autenticação: {result.error}")
            return False

        print(f"✅ Sessão iniciada: {result.output.get('session_token', '')[:20]}...")

        # Test get tickets
        print("\n2️⃣ Buscando últimos 5 tickets...")
        result = await client.get_tickets(limit=5)

        if not result.success:
            print(f"❌ Falha ao buscar tickets: {result.error}")
            return False

        tickets = result.output.get('tickets', [])
        print(f"✅ Encontrados {len(tickets)} tickets")

        if tickets:
            print("\n📋 Exemplos de tickets:")
            for ticket in tickets[:3]:
                ticket_id = ticket.get('id', 'N/A')
                name = ticket.get('name', 'Sem título')
                status = ticket.get('status', 'N/A')
                print(f"   • #{ticket_id}: {name[:50]} (Status: {status})")

        # Kill session
        await client.kill_session()
        await client.close()

        print("\n✅ GLPI Integration: OK")
        return True

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        await client.close()
        return False


async def test_zabbix():
    """Test Zabbix integration."""
    print("\n" + "="*60)
    print("🔍 Testando Zabbix Integration")
    print("="*60)

    settings = get_settings()

    if not settings.zabbix.enabled:
        print("❌ Zabbix não está habilitado")
        return False

    print(f"📡 Base URL: {settings.zabbix.base_url}")
    print(f"🔑 API Token: {settings.zabbix.api_token[:20]}...")

    client = ZabbixClient(settings.zabbix)

    try:
        # Test get problems
        print("\n1️⃣ Buscando problemas ativos...")
        result = await client.get_problems(limit=5, severity=3)

        if not result.success:
            print(f"❌ Falha ao buscar problemas: {result.error}")
            return False

        problems = result if isinstance(result, list) else []
        print(f"✅ Encontrados {len(problems)} problemas")

        if problems:
            print("\n⚠️ Exemplos de problemas:")
            for problem in problems[:3]:
                event_id = problem.get('eventid', 'N/A')
                name = problem.get('name', 'Sem nome')
                severity = problem.get('severity', 'N/A')
                print(f"   • Event #{event_id}: {name[:50]} (Severity: {severity})")

        await client.close()

        print("\n✅ Zabbix Integration: OK")
        return True

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        await client.close()
        return False


async def test_linear():
    """Test Linear integration."""
    print("\n" + "="*60)
    print("🔍 Testando Linear Integration")
    print("="*60)

    settings = get_settings()

    if not settings.linear.enabled:
        print("❌ Linear não está habilitado")
        return False

    print(f"🔑 API Key: {settings.linear.api_key[:20]}...")

    client = LinearClient(settings.linear.api_key)

    try:
        # Test get teams
        print("\n1️⃣ Buscando teams...")
        result = await client.get_teams()

        if not result.success:
            print(f"❌ Falha ao buscar teams: {result.error}")
            return False

        teams = result.output.get('teams', [])
        print(f"✅ Encontrados {len(teams)} teams")

        if teams:
            print("\n👥 Teams disponíveis:")
            for team in teams:
                team_id = team.get('id', 'N/A')
                name = team.get('name', 'Sem nome')
                key = team.get('key', 'N/A')
                print(f"   • {key}: {name} (ID: {team_id[:8]}...)")

        # Test get issues
        print("\n2️⃣ Buscando últimas 5 issues...")
        result = await client.get_issues(limit=5)

        if not result.success:
            print(f"❌ Falha ao buscar issues: {result.error}")
            return False

        issues = result.output.get('issues', [])
        print(f"✅ Encontradas {len(issues)} issues")

        if issues:
            print("\n📋 Exemplos de issues:")
            for issue in issues[:3]:
                identifier = issue.get('identifier', 'N/A')
                title = issue.get('title', 'Sem título')
                state = issue.get('state', {}).get('name', 'N/A')
                print(f"   • {identifier}: {title[:50]} (State: {state})")

        await client.close()

        print("\n✅ Linear Integration: OK")
        return True

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        await client.close()
        return False


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test integrations")
    parser.add_argument('--glpi', action='store_true', help='Test only GLPI')
    parser.add_argument('--zabbix', action='store_true', help='Test only Zabbix')
    parser.add_argument('--linear', action='store_true', help='Test only Linear')
    parser.add_argument('--all', action='store_true', help='Test all integrations')

    args = parser.parse_args()

    print("\n" + "🚀 DeepCode VSA - Integration Tests".center(60, "="))
    print("Hospital Evangélico - Ambiente de Produção")
    print("="*60)

    results = {}

    # If no specific flag, test all
    if not (args.glpi or args.zabbix or args.linear):
        args.all = True

    if args.all or args.glpi:
        results['GLPI'] = await test_glpi()

    if args.all or args.zabbix:
        results['Zabbix'] = await test_zabbix()

    if args.all or args.linear:
        results['Linear'] = await test_linear()

    # Summary
    print("\n" + "="*60)
    print("📊 Resumo dos Testes")
    print("="*60)

    all_passed = True
    for service, passed in results.items():
        status = "✅ OK" if passed else "❌ FALHA"
        print(f"{service:.<40} {status}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 Todas as integrações funcionando corretamente!")
        return 0
    else:
        print("\n⚠️ Algumas integrações falharam. Verifique as configurações.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
