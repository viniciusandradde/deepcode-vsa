'use client';

import { useEffect, useState } from 'react';
import { getQueueStats } from '@/lib/api/scheduler';

// Formato real da API Celery Flower
interface CeleryWorkerStats {
    active: number;
    scheduled: number;
    reserved: number;
    stats?: {
        total?: Record<string, number>;
    };
}

interface ParsedStats {
    active: number;
    scheduled: number;
    reserved: number;
    workerName: string;
}

/**
 * Widget that displays current queue statistics from Celery
 */
export function TaskMonitor() {
    const [stats, setStats] = useState<ParsedStats | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const parseStats = (rawData: unknown): ParsedStats | null => {
        try {
            // A API retorna objeto com chave dinâmica: { "celery@hostname": { active: [], ... } }
            if (!rawData || typeof rawData !== 'object') return null;

            const workerKeys = Object.keys(rawData as Record<string, unknown>);
            if (workerKeys.length === 0) return null;

            const workerName = workerKeys[0];
            const workerData = (rawData as Record<string, CeleryWorkerStats>)[workerName];

            if (!workerData) return null;

            // 'active', 'scheduled', 'reserved' são arrays de tasks no Celery Flower
            const active = Array.isArray(workerData.active) ? workerData.active.length : (workerData.active || 0);
            const scheduled = Array.isArray(workerData.scheduled) ? workerData.scheduled.length : (workerData.scheduled || 0);
            const reserved = Array.isArray(workerData.reserved) ? workerData.reserved.length : (workerData.reserved || 0);

            return {
                active: typeof active === 'number' ? active : 0,
                scheduled: typeof scheduled === 'number' ? scheduled : 0,
                reserved: typeof reserved === 'number' ? reserved : 0,
                workerName: workerName.replace('celery@', ''),
            };
        } catch {
            return null;
        }
    };

    const fetchStats = async () => {
        try {
            const data = await getQueueStats();
            const parsed = parseStats(data);
            if (parsed) {
                setStats(parsed);
                setError(null);
            } else {
                setError('Formato de resposta inválido');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Falha ao carregar');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 10000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 animate-pulse">
                <div className="h-4 bg-zinc-800 rounded w-1/3 mb-3"></div>
                <div className="grid grid-cols-3 gap-2">
                    <div className="h-12 bg-zinc-800 rounded"></div>
                    <div className="h-12 bg-zinc-800 rounded"></div>
                    <div className="h-12 bg-zinc-800 rounded"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4 text-amber-400">
                <p className="text-sm font-medium">⚠️ Worker Celery</p>
                <p className="text-xs opacity-70 mt-1">{error}</p>
            </div>
        );
    }

    if (!stats) return null;

    const totalActive = stats.active + stats.reserved;

    return (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-zinc-300">📊 Fila de Tarefas</h3>
                <span className="text-xs text-zinc-500">{stats.workerName}</span>
            </div>

            <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-3 rounded-md bg-zinc-800/50">
                    <p className="text-2xl font-bold text-emerald-400">{totalActive}</p>
                    <p className="text-xs text-zinc-500 mt-1">Ativas</p>
                </div>
                <div className="text-center p-3 rounded-md bg-zinc-800/50">
                    <p className="text-2xl font-bold text-amber-400">{stats.scheduled}</p>
                    <p className="text-xs text-zinc-500 mt-1">Agendadas</p>
                </div>
                <div className="text-center p-3 rounded-md bg-zinc-800/50">
                    <p className="text-2xl font-bold text-blue-400">{stats.reserved}</p>
                    <p className="text-xs text-zinc-500 mt-1">Reservadas</p>
                </div>
            </div>
        </div>
    );
}
