import Link from 'next/link';
import { ScheduleForm } from '@/components/automation';

export const metadata = {
    title: 'Novo Agendamento | DeepCode VSA',
    description: 'Crie um novo agendamento de prompt automático',
};

export default function NewSchedulePage() {
    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100">
            <div className="max-w-2xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <Link
                        href="/automation/scheduler"
                        className="text-zinc-500 hover:text-zinc-300 text-sm flex items-center gap-1 mb-4"
                    >
                        ← Voltar para Scheduler
                    </Link>
                    <h1 className="text-2xl font-bold text-zinc-100">➕ Novo Agendamento</h1>
                    <p className="text-zinc-500 mt-1">
                        Configure um prompt para ser executado automaticamente
                    </p>
                </div>

                {/* Form Card */}
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
                    <ScheduleForm />
                </div>

                {/* Help Section */}
                <div className="mt-6 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                    <h3 className="text-sm font-medium text-zinc-300 mb-2">💡 Dicas</h3>
                    <ul className="text-sm text-zinc-500 space-y-1">
                        <li>• O agente terá acesso às ferramentas GLPI, Zabbix e Linear</li>
                        <li>• Use expressões CRON para controlar a frequência</li>
                        <li>• Configure o Telegram Bot Token nas variáveis de ambiente para usar o padrão</li>
                        <li>• Os resultados serão enviados para o canal configurado</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
