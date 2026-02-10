'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listSchedules, deleteSchedule, pauseSchedule, resumeSchedule, runSchedule } from '@/lib/api/scheduler';
import type { Schedule } from '@/types/automation';
import { useToast } from '@/components/ui/toast';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

/**
 * Converte expressão CRON para texto legível
 * Suporta formato CRON padrão e formato APScheduler (ex: cron[month='*', ...])
 */
function cronToHuman(cron: string): string {
    // Formato APScheduler: cron[month='*', day='*', day_of_week='*', hour='9', minute='0']
    if (cron.includes("cron[") || cron.includes("hour='") || cron.includes("minute='")) {
        // Extrair valores usando regex mais específicos
        const hourMatch = cron.match(/hour='([^']+)'/);
        const minuteMatch = cron.match(/minute='([^']+)'/);
        const dowMatch = cron.match(/day_of_week='([^']+)'/);

        const hour = hourMatch ? hourMatch[1] : '*';
        const minute = minuteMatch ? minuteMatch[1] : '*';
        const dow = dowMatch ? dowMatch[1] : '*';

        return formatSchedule(minute, hour, dow);
    }

    // Formato CRON padrão: minuto hora dia mês dia_da_semana
    const parts = cron.trim().split(/\s+/);
    if (parts.length >= 5) {
        const [minute, hour, , , dayOfWeek] = parts;
        return formatSchedule(minute, hour, dayOfWeek);
    }

    // Fallback - tentar extrair qualquer padrão hora:minuto
    const timeMatch = cron.match(/(\d{1,2}):(\d{2})/);
    if (timeMatch) {
        return `Às ${timeMatch[1].padStart(2, '0')}:${timeMatch[2]}`;
    }

    return "Agendado"; // Fallback genérico
}

function formatSchedule(minute: string, hour: string, dayOfWeek: string): string {
    const dowNames: Record<string, string> = {
        '0': 'Dom', '1': 'Seg', '2': 'Ter', '3': 'Qua',
        '4': 'Qui', '5': 'Sex', '6': 'Sáb',
        'sun': 'Dom', 'mon': 'Seg', 'tue': 'Ter', 'wed': 'Qua',
        'thu': 'Qui', 'fri': 'Sex', 'sat': 'Sáb',
        '*': ''
    };

    // Tratar intervalos como */5
    if (minute.includes('/')) {
        const interval = minute.split('/')[1];
        return `A cada ${interval} min`;
    }

    if (hour.includes('/')) {
        const interval = hour.split('/')[1];
        return `A cada ${interval}h`;
    }

    // Formatar horário
    const time = hour !== '*' && minute !== '*'
        ? `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
        : hour !== '*'
            ? `${hour.padStart(2, '0')}:00`
            : 'A cada hora';

    // Se não tem dia da semana específico
    if (dayOfWeek === '*' || dayOfWeek === '') {
        if (time === 'A cada hora') return time;
        return `Diário às ${time}`;
    }

    // Mapear dia da semana
    const dowParts = dayOfWeek.toLowerCase().split(',').map(d => {
        const trimmed = d.trim();
        return dowNames[trimmed] || trimmed;
    });

    if (dowParts.length === 1 && dowParts[0]) {
        return `${dowParts[0]} às ${time}`;
    }

    if (dowParts.filter(Boolean).length > 0) {
        return `${dowParts.filter(Boolean).join(', ')} às ${time}`;
    }

    return `Diário às ${time}`;
}

/**
 * Table/Grid displaying active scheduled jobs
 */
export function ScheduleList() {
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState<Record<string, string | null>>({});
    const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
    const { addToast } = useToast();

    const setActionState = (id: string, action: string | null) => {
        setActionLoading((prev) => ({ ...prev, [id]: action }));
    };

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

    const handleDelete = async () => {
        if (!deleteTarget) return;
        const { id, name } = deleteTarget;
        setDeleteTarget(null);
        setActionState(id, 'delete');
        try {
            await deleteSchedule(id);
            setSchedules(prev => prev.filter(s => s.id !== id));
            addToast(`"${name}" removido`, 'success');
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Erro ao remover', 'error');
        } finally {
            setActionState(id, null);
        }
    };

    const handlePause = async (id: string) => {
        setActionState(id, 'pause');
        try {
            await pauseSchedule(id);
            await fetchSchedules();
            addToast('Agendamento pausado', 'success');
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Erro ao pausar', 'error');
        } finally {
            setActionState(id, null);
        }
    };

    const handleResume = async (id: string) => {
        setActionState(id, 'resume');
        try {
            await resumeSchedule(id);
            await fetchSchedules();
            addToast('Agendamento retomado', 'success');
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Erro ao retomar', 'error');
        } finally {
            setActionState(id, null);
        }
    };

    const handleRun = async (id: string, name: string) => {
        setActionState(id, 'run');
        try {
            await runSchedule(id);
            addToast(`Tarefa "${name}" disparada com sucesso`, 'success');
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Erro ao executar', 'error');
        } finally {
            setActionState(id, null);
        }
    };

    if (loading) {
        return (
            <div className="rounded-lg border border-white/[0.06] bg-obsidian-800 p-6">
                <div className="animate-pulse space-y-3">
                    <div className="h-4 bg-obsidian-800 rounded w-1/4"></div>
                    <div className="h-10 bg-obsidian-800 rounded"></div>
                    <div className="h-10 bg-obsidian-800 rounded"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-4 text-red-300">
                <p className="font-medium">Erro ao carregar agendamentos</p>
                <p className="text-sm opacity-70 mt-1">{error}</p>
                <button onClick={fetchSchedules} className="mt-2 text-sm underline">Tentar novamente</button>
            </div>
        );
    }

    if (schedules.length === 0) {
        return (
            <div className="rounded-lg border border-white/[0.06] bg-obsidian-800 p-8 text-center">
                <p className="text-neutral-500 text-lg">Nenhum agendamento ativo</p>
                <p className="text-neutral-600 text-sm mt-2">Crie um novo agendamento para começar</p>
            </div>
        );
    }

    return (
        <>
            <div className="rounded-lg border border-white/[0.06] bg-obsidian-800 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-white/5">
                        <tr className="text-neutral-400 text-left">
                            <th className="px-4 py-3 font-medium">Nome</th>
                            <th className="px-4 py-3 font-medium">Frequência</th>
                            <th className="px-4 py-3 font-medium">Canal</th>
                            <th className="px-4 py-3 font-medium">Próxima Execução</th>
                            <th className="px-4 py-3 font-medium text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.06]">
                        {schedules.map((schedule) => {
                            const busy = actionLoading[schedule.id];
                            return (
                                <tr key={schedule.id} className="hover:bg-white/5 transition-colors">
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <span className={`w-2 h-2 rounded-full ${schedule.enabled ? 'bg-emerald-500' : 'bg-neutral-500'}`}></span>
                                            <span className="text-white font-medium">{schedule.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="text-neutral-300 text-sm">
                                            {cronToHuman(schedule.cron)}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="px-2 py-1 rounded text-xs bg-obsidian-800 text-neutral-300 capitalize">
                                            {schedule.config.channel}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-neutral-400 text-xs">
                                        {schedule.next_run
                                            ? new Date(schedule.next_run).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
                                            : '-'
                                        }
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => handleRun(schedule.id, schedule.name)}
                                                disabled={!!busy}
                                                className="px-2 py-1 text-xs rounded bg-cyan-900/30 text-cyan-400 hover:bg-cyan-900/50 transition-colors disabled:opacity-50"
                                            >
                                                {busy === 'run' ? 'Disparando...' : 'Testar'}
                                            </button>
                                            <Link
                                                href={`/automation/scheduler/${encodeURIComponent(schedule.id)}/edit`}
                                                className="px-2 py-1 text-xs rounded bg-blue-900/30 text-blue-400 hover:bg-blue-900/50 transition-colors"
                                            >
                                                Editar
                                            </Link>
                                            {schedule.enabled ? (
                                                <button
                                                    onClick={() => handlePause(schedule.id)}
                                                    disabled={!!busy}
                                                    className="px-2 py-1 text-xs rounded bg-amber-900/30 text-amber-400 hover:bg-amber-900/50 transition-colors disabled:opacity-50"
                                                >
                                                    {busy === 'pause' ? 'Pausando...' : 'Pausar'}
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => handleResume(schedule.id)}
                                                    disabled={!!busy}
                                                    className="px-2 py-1 text-xs rounded bg-emerald-900/30 text-emerald-400 hover:bg-emerald-900/50 transition-colors disabled:opacity-50"
                                                >
                                                    {busy === 'resume' ? 'Retomando...' : 'Retomar'}
                                                </button>
                                            )}
                                            <button
                                                onClick={() => setDeleteTarget({ id: schedule.id, name: schedule.name })}
                                                disabled={!!busy}
                                                className="px-2 py-1 text-xs rounded bg-red-900/30 text-red-400 hover:bg-red-900/50 transition-colors disabled:opacity-50"
                                            >
                                                {busy === 'delete' ? '...' : 'Remover'}
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            <Dialog
                open={!!deleteTarget}
                onClose={() => setDeleteTarget(null)}
                title="Confirmar exclusão"
                footer={
                    <>
                        <Button variant="outline" onClick={() => setDeleteTarget(null)} className="border-white/10 text-neutral-300">
                            Cancelar
                        </Button>
                        <Button onClick={handleDelete} className="bg-red-600 hover:bg-red-700 text-white">
                            Remover
                        </Button>
                    </>
                }
            >
                Tem certeza que deseja remover o agendamento <strong>&quot;{deleteTarget?.name}&quot;</strong>?
            </Dialog>
        </>
    );
}
