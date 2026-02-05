'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createSchedule } from '@/lib/api/scheduler';
import type { ScheduleCreateRequest, ScheduleConfig } from '@/types/automation';

const CRON_PRESETS = [
    { label: 'A cada hora', value: '0 * * * *' },
    { label: 'Diário às 9h', value: '0 9 * * *' },
    { label: 'Diário às 18h', value: '0 18 * * *' },
    { label: 'Segunda às 9h', value: '0 9 * * 1' },
    { label: 'Sexta às 17h', value: '0 17 * * 5' },
    { label: 'A cada 5 min (teste)', value: '*/5 * * * *' },
];

const CHANNEL_OPTIONS = [
    { value: 'telegram', label: '💬 Telegram', icon: '💬' },
    { value: 'teams', label: '🟦 Microsoft Teams', icon: '🟦' },
    { value: 'whatsapp', label: '💚 WhatsApp', icon: '💚' },
];

interface ScheduleFormProps {
    onSuccess?: () => void;
}

export function ScheduleForm({ onSuccess }: ScheduleFormProps) {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [name, setName] = useState('');
    const [prompt, setPrompt] = useState('');
    const [cron, setCron] = useState('0 9 * * *');
    const [channel, setChannel] = useState<ScheduleConfig['channel']>('telegram');
    const [targetId, setTargetId] = useState('');
    const [token, setToken] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const payload: ScheduleCreateRequest = {
                name,
                prompt,
                cron,
                config: {
                    channel,
                    target_id: targetId,
                    credentials: token ? { token } : undefined,
                },
                enabled: true,
            };

            await createSchedule(payload);

            if (onSuccess) {
                onSuccess();
            } else {
                router.push('/automation/scheduler');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar agendamento');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
                <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-4 text-red-400">
                    <p className="font-medium">❌ Erro</p>
                    <p className="text-sm opacity-70 mt-1">{error}</p>
                </div>
            )}

            {/* Nome */}
            <div>
                <label htmlFor="name" className="block text-sm font-medium text-zinc-300 mb-2">
                    Nome do Agendamento
                </label>
                <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ex: Relatório Semanal de Tasks"
                    required
                    className="w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                />
            </div>

            {/* Prompt */}
            <div>
                <label htmlFor="prompt" className="block text-sm font-medium text-zinc-300 mb-2">
                    Instrução para o Agente
                </label>
                <textarea
                    id="prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Descreva a tarefa que o agente deve executar..."
                    required
                    rows={4}
                    className="w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 resize-none"
                />
                <p className="text-xs text-zinc-500 mt-1">
                    O agente terá acesso às ferramentas GLPI, Zabbix e Linear para executar esta tarefa.
                </p>
            </div>

            {/* CRON */}
            <div>
                <label htmlFor="cron" className="block text-sm font-medium text-zinc-300 mb-2">
                    Frequência (CRON)
                </label>
                <div className="flex gap-2 mb-2 flex-wrap">
                    {CRON_PRESETS.map((preset) => (
                        <button
                            key={preset.value}
                            type="button"
                            onClick={() => setCron(preset.value)}
                            className={`px-3 py-1 text-xs rounded-full transition-colors ${cron === preset.value
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                }`}
                        >
                            {preset.label}
                        </button>
                    ))}
                </div>
                <input
                    id="cron"
                    type="text"
                    value={cron}
                    onChange={(e) => setCron(e.target.value)}
                    placeholder="* * * * *"
                    required
                    className="w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                />
                <p className="text-xs text-zinc-500 mt-1">
                    Formato: minuto hora dia mês dia_da_semana
                </p>
            </div>

            {/* Canal de Notificação */}
            <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Canal de Notificação
                </label>
                <div className="grid grid-cols-3 gap-2">
                    {CHANNEL_OPTIONS.map((opt) => (
                        <button
                            key={opt.value}
                            type="button"
                            onClick={() => setChannel(opt.value as ScheduleConfig['channel'])}
                            className={`p-3 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${channel === opt.value
                                    ? 'bg-emerald-600/20 border-2 border-emerald-500 text-emerald-400'
                                    : 'bg-zinc-800 border-2 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                                }`}
                        >
                            <span>{opt.icon}</span>
                            <span>{opt.value}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Target ID */}
            <div>
                <label htmlFor="targetId" className="block text-sm font-medium text-zinc-300 mb-2">
                    {channel === 'telegram' && 'Chat ID do Telegram'}
                    {channel === 'teams' && 'Webhook URL do Teams'}
                    {channel === 'whatsapp' && 'Número do WhatsApp'}
                </label>
                <input
                    id="targetId"
                    type="text"
                    value={targetId}
                    onChange={(e) => setTargetId(e.target.value)}
                    placeholder={
                        channel === 'telegram' ? 'Ex: 123456789' :
                            channel === 'teams' ? 'https://outlook.office.com/webhook/...' :
                                '+5511999999999'
                    }
                    required
                    className="w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                />
            </div>

            {/* Token (opcional para alguns canais) */}
            {channel === 'telegram' && (
                <div>
                    <label htmlFor="token" className="block text-sm font-medium text-zinc-300 mb-2">
                        Bot Token (opcional - usa default se vazio)
                    </label>
                    <input
                        id="token"
                        type="password"
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                        placeholder="Deixe vazio para usar o bot padrão"
                        className="w-full px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                    />
                </div>
            )}

            {/* Submit */}
            <div className="flex gap-3 pt-4">
                <button
                    type="button"
                    onClick={() => router.back()}
                    className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 transition-colors"
                >
                    Cancelar
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {loading ? 'Criando...' : '✅ Criar Agendamento'}
                </button>
            </div>
        </form>
    );
}
