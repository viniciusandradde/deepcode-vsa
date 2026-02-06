'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getSchedule } from '@/lib/api/scheduler';
import { ScheduleForm } from '@/components/automation/ScheduleForm';
import type { Schedule, ScheduleConfig } from '@/types/automation';

export default function EditSchedulePage() {
    const params = useParams();
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [scheduleId, setScheduleId] = useState<string>('');
    const [initialData, setInitialData] = useState<{
        name: string;
        prompt: string;
        cron: string;
        channel: ScheduleConfig['channel'];
        targetId: string;
    } | undefined>(undefined);

    useEffect(() => {
        const id = params.id as string;
        if (!id) {
            setError('ID do agendamento não encontrado');
            setLoading(false);
            return;
        }

        const decodedId = decodeURIComponent(id);
        setScheduleId(decodedId);

        // Carregar dados do agendamento
        async function loadSchedule() {
            try {
                const schedule = await getSchedule(decodedId);

                // Extrair expressão CRON do formato APScheduler se necessário
                let cronExpression = schedule.cron;
                if (cronExpression.includes("cron[")) {
                    // Tentar converter de volta para CRON padrão
                    const hourMatch = cronExpression.match(/hour='([^']+)'/);
                    const minuteMatch = cronExpression.match(/minute='([^']+)'/);
                    const dowMatch = cronExpression.match(/day_of_week='([^']+)'/);
                    const dayMatch = cronExpression.match(/day='([^']+)'/);
                    const monthMatch = cronExpression.match(/month='([^']+)'/);

                    const minute = minuteMatch ? minuteMatch[1] : '*';
                    const hour = hourMatch ? hourMatch[1] : '*';
                    const day = dayMatch ? dayMatch[1] : '*';
                    const month = monthMatch ? monthMatch[1] : '*';
                    const dow = dowMatch ? dowMatch[1] : '*';

                    cronExpression = `${minute} ${hour} ${day} ${month} ${dow}`;
                }

                setInitialData({
                    name: schedule.name,
                    prompt: schedule.prompt,
                    cron: cronExpression,
                    channel: schedule.config.channel,
                    targetId: schedule.config.target_id,
                });
                setLoading(false);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Erro ao carregar agendamento');
                setLoading(false);
            }
        }

        loadSchedule();
    }, [params.id]);

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
                <div className="animate-pulse text-zinc-500">Carregando agendamento...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
                <div className="max-w-2xl mx-auto">
                    <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4 text-red-400">
                        <p className="font-medium">❌ Erro</p>
                        <p className="text-sm opacity-70 mt-1">{error}</p>
                        <button
                            onClick={() => router.push('/automation/scheduler')}
                            className="mt-4 px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                        >
                            Voltar
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100">
            <div className="max-w-2xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <button
                        onClick={() => router.back()}
                        className="text-zinc-500 hover:text-zinc-300 text-sm mb-4 flex items-center gap-1"
                    >
                        ← Voltar
                    </button>
                    <h1 className="text-2xl font-bold text-zinc-100">✏️ Editar Agendamento</h1>
                    <p className="text-zinc-500 mt-1 text-sm">{initialData?.name || scheduleId}</p>
                </div>

                {/* Form */}
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
                    <ScheduleForm
                        editMode
                        scheduleId={scheduleId}
                        initialData={initialData}
                        onSuccess={() => router.push('/automation/scheduler')}
                    />
                </div>
            </div>
        </div>
    );
}
