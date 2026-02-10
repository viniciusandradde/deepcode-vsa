import { ScheduleForm } from '@/components/automation';
import { PageNavBar } from '@/components/app/PageNavBar';

export const metadata = {
    title: 'Novo Agendamento | DeepCode VSA',
    description: 'Crie um novo agendamento de prompt automático',
};

export default function NewSchedulePage() {
    return (
        <div className="min-h-screen bg-obsidian-950 text-white">
            <PageNavBar breadcrumbs={[
                { label: "Scheduler", href: "/automation/scheduler" },
                { label: "Novo Agendamento" },
            ]} />
            <div className="max-w-2xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white">Novo Agendamento</h1>
                    <p className="text-neutral-500 mt-1">
                        Configure um prompt para ser executado automaticamente
                    </p>
                </div>

                {/* Form Card */}
                <div className="rounded-xl border border-white/[0.06] bg-obsidian-800 p-6">
                    <ScheduleForm />
                </div>

                {/* Help Section */}
                <div className="mt-6 rounded-lg border border-white/[0.06] bg-obsidian-800/50 p-4">
                    <h3 className="text-sm font-medium text-neutral-300 mb-2">Dicas</h3>
                    <ul className="text-sm text-neutral-500 space-y-1">
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
