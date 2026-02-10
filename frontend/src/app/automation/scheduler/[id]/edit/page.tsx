'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getSchedule } from '@/lib/api/scheduler';
import { ScheduleForm } from '@/components/automation/ScheduleForm';
import type { Schedule, ScheduleConfig } from '@/types/automation';
import { PageNavBar } from '@/components/app/PageNavBar';

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
            <div className="min-h-screen bg-obsidian-950 text-white flex items-center justify-center">
                <div className="animate-pulse text-neutral-500">Carregando agendamento...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-obsidian-950 text-white p-8">
                <div className="max-w-2xl mx-auto">
                    <div className="rounded-lg border border-red-500/30 bg-red-900/20 p-4 text-red-300">
                        <p className="font-medium">Erro</p>
                        <p className="text-sm opacity-70 mt-1">{error}</p>
                        <button
                            onClick={() => router.push('/automation/scheduler')}
                            className="mt-4 px-4 py-2 rounded-lg bg-obsidian-800 text-neutral-300 hover:bg-white/10"
                        >
                            Voltar
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-obsidian-950 text-white">
            <PageNavBar breadcrumbs={[
                { label: "Scheduler", href: "/automation/scheduler" },
                { label: "Editar Agendamento" },
            ]} />
            <div className="max-w-2xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-white">Editar Agendamento</h1>
                    <p className="text-neutral-500 mt-1 text-sm">{initialData?.name || scheduleId}</p>
                </div>

                {/* Form */}
                <div className="rounded-lg border border-white/[0.06] bg-obsidian-800 p-6">
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
