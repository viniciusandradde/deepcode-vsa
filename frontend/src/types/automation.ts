/**
 * Types for the Automation/Scheduler system
 * Matches backend Pydantic models in api/models/automation.py
 */

export interface ScheduleConfig {
    channel: 'telegram' | 'teams' | 'whatsapp';
    target_id: string;
    credentials?: Record<string, string>;
}

export interface Schedule {
    id: string;
    name: string;
    prompt: string;
    cron: string;
    config: ScheduleConfig;
    enabled: boolean;
    next_run: string | null;
    created_at: string;
}

export interface ScheduleCreateRequest {
    name: string;
    prompt: string;
    cron: string;
    config: ScheduleConfig;
    enabled?: boolean;
}

export interface ScheduleListResponse {
    schedules: Schedule[];
    total: number;
}

export interface QueueStats {
    active: number;
    reserved: number;
    scheduled: number;
    queues: {
        agent: number;
        reports: number;
        notifications: number;
    };
}

export interface TaskInfo {
    task_id: string;
    status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'REVOKED';
    result?: unknown;
    error?: string;
}
