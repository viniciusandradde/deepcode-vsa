'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listSchedules, deleteSchedule, pauseSchedule, resumeSchedule, runSchedule } from '@/lib/api/scheduler';
import type { Schedule } from '@/types/automation';

/**
 * Converte expressão CRON para texto legível
 */
function cronToHuman(cron: string): string {
    // Formato: minuto hora dia mês dia_da_semana
    // Também aceita formato APScheduler: cron[month='*', day='*', day_of_week='*', hour='9', minute='0']

    // Tentar extrair de formato APScheduler
    const apMatch = cron.match(/hour='(\d+|\*)'.*minute='(\d+|\*)'/i);
    if (apMatch) {
        const hour = apMatch[1];
        const minute = apMatch[2];

        const dayMatch = cron.match(/day_of_week='([^']+)'/i);
        const dow = dayMatch ? dayMatch[1] : '*';

        return formatSchedule(minute, hour, dow);
    }

    // Formato CRON padrão
    const parts = cron.trim().split(/\s+/);
    if (parts.length >= 5) {
        const [minute, hour, , , dayOfWeek] = parts;
        return formatSchedule(minute, hour, dayOfWeek);
    }

    return cron; // Fallback
}

function formatSchedule(minute: string, hour: string, dayOfWeek: string): string {
    const dowNames: Record<string, string> = {
        '0': 'Dom', '1': 'Seg', '2': 'Ter', '3': 'Qua',
        '4': 'Qui', '5': 'Sex', '6': 'Sáb', '*': ''
    };

    const time = hour !== '*' && minute !== '*'
        ? `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
        : 'A cada hora';

    if (dayOfWeek === '*') {
        return `Diário às ${time}`;
    }

    const dowParts = dayOfWeek.split(',').map(d => dowNames[d.trim()] || d);
    if (dowParts.length === 1) {
        return `${dowParts[0]} às ${time}`;
    }

    return `${dowParts.join(', ')} às ${time}`;
}

/**
 * Table/Grid displaying active scheduled jobs
 */
export function ScheduleList() {
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSchedules = async () => {
        try {
            const data = await listSchedules();
            setSchedules(data.schedules);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load schedules');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSchedules();
    }, []);

    const handleDelete = async (id: string) => {
        if (!confirm('Tem certeza que deseja remover este agendamento?')) return;
        try {
            await deleteSchedule(id);
            setSchedules(prev => prev.filter(s => s.id !== id));
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Erro ao remover');
        }
    };

    const handlePause = async (id: string) => {
        try {
            await pauseSchedule(id);
            fetchSchedules();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Erro ao pausar');
        }
    };

    const handleResume = async (id: string) => {
        try {
            await resumeSchedule(id);
            fetchSchedules();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Erro ao retomar');
        }
    };

    const handleRun = async (id: string, name: string) => {
        try {
            const result = await runSchedule(id);
            alert(`🚀 Tarefa "${name}" disparada!\nTask ID: ${result.task_id}`);
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Erro ao executar');
        }
    };

    if (loading) {
        return (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
                <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-zinc-800 rounded w-1/4"></div>
                    <div className="h-10 bg-zinc-800 rounded"></div>
                    <div className="h-10 bg-zinc-800 rounded"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4 text-red-400">
                <p className="font-medium">❌ Erro ao carregar agendamentos</p>
                <p className="text-sm opacity-70 mt-1">{error}</p>
                <button onClick={fetchSchedules} className="mt-2 text-sm underline">Tentar novamente</button>
            </div>
        );
    }

    if (schedules.length === 0) {
        return (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-8 text-center">
                <p className="text-zinc-500 text-lg">📅 Nenhum agendamento ativo</p>
                <p className="text-zinc-600 text-sm mt-2">Crie um novo agendamento para começar</p>
            </div>
        );
    }

    return (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 overflow-hidden">
            <table className="w-full text-sm">
                <thead className="bg-zinc-800/50">
                    <tr className="text-zinc-400 text-left">
                        <th className="px-4 py-3 font-medium">Nome</th>
                        <th className="px-4 py-3 font-medium">Frequência</th>
                        <th className="px-4 py-3 font-medium">Canal</th>
                        <th className="px-4 py-3 font-medium">Próxima Execução</th>
                        <th className="px-4 py-3 font-medium text-right">Ações</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                    {schedules.map((schedule) => (
                        <tr key={schedule.id} className="hover:bg-zinc-800/30 transition-colors">
                            <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <span className={`w-2 h-2 rounded-full ${schedule.enabled ? 'bg-emerald-500' : 'bg-zinc-500'}`}></span>
                                    <span className="text-zinc-200 font-medium">{schedule.name}</span>
                                </div>
                            </td>
                            <td className="px-4 py-3">
                                <span className="text-zinc-300 text-sm">
                                    🕐 {cronToHuman(schedule.cron)}
                                </span>
                            </td>
                            <td className="px-4 py-3">
                                <span className="px-2 py-1 rounded text-xs bg-zinc-800 text-zinc-300 capitalize">
                                    {schedule.config.channel === 'telegram' && '💬 '}
                                    {schedule.config.channel === 'teams' && '🟦 '}
                                    {schedule.config.channel === 'whatsapp' && '💚 '}
                                    {schedule.config.channel}
                                </span>
                            </td>
                            <td className="px-4 py-3 text-zinc-400 text-xs">
                                {schedule.next_run
                                    ? new Date(schedule.next_run).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
                                    : '-'
                                }
                            </td>
                            <td className="px-4 py-3 text-right">
                                <div className="flex items-center justify-end gap-2">
                                    <button
                                        onClick={() => handleRun(schedule.id, schedule.name)}
                                        className="px-2 py-1 text-xs rounded bg-cyan-900/30 text-cyan-400 hover:bg-cyan-900/50 transition-colors"
                                    >
                                        🚀 Testar
                                    </button>
                                    <Link
                                        href={`/automation/scheduler/${encodeURIComponent(schedule.id)}/edit`}
                                        className="px-2 py-1 text-xs rounded bg-blue-900/30 text-blue-400 hover:bg-blue-900/50 transition-colors"
                                    >
                                        ✏️ Editar
                                    </Link>
                                    {schedule.enabled ? (
                                        <button
                                            onClick={() => handlePause(schedule.id)}
                                            className="px-2 py-1 text-xs rounded bg-amber-900/30 text-amber-400 hover:bg-amber-900/50 transition-colors"
                                        >
                                            ⏸️ Pausar
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => handleResume(schedule.id)}
                                            className="px-2 py-1 text-xs rounded bg-emerald-900/30 text-emerald-400 hover:bg-emerald-900/50 transition-colors"
                                        >
                                            ▶️ Retomar
                                        </button>
                                    )}
                                    <button
                                        onClick={() => handleDelete(schedule.id)}
                                        className="px-2 py-1 text-xs rounded bg-red-900/30 text-red-400 hover:bg-red-900/50 transition-colors"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
