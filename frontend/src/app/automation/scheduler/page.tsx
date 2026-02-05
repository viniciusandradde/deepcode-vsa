import Link from 'next/link';
import { TaskMonitor, ScheduleList } from '@/components/automation';

export const metadata = {
    title: 'Scheduler | DeepCode VSA',
    description: 'Gerencie agendamentos de prompts automáticos',
};

export default function SchedulerPage() {
    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100">
            <div className="max-w-6xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold text-zinc-100">📅 Scheduler</h1>
                        <p className="text-zinc-500 mt-1">Gerencie agendamentos de prompts automáticos</p>
                    </div>
                    <Link
                        href="/automation/scheduler/new"
                        className="px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium hover:bg-emerald-500 transition-colors flex items-center gap-2"
                    >
                        <span>➕</span>
                        <span>Novo Agendamento</span>
                    </Link>
                </div>

                {/* Task Monitor Widget */}
                <div className="mb-6">
                    <TaskMonitor />
                </div>

                {/* Schedule List */}
                <div>
                    <h2 className="text-lg font-semibold text-zinc-300 mb-4">Agendamentos Ativos</h2>
                    <ScheduleList />
                </div>
            </div>
        </div>
    );
}
