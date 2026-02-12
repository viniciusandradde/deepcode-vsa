/**
 * API client for the Automation/Scheduler system
 * Communicates with backend endpoints in api/routes/automation.py and api/routes/queue.py
 */

import type {
    Schedule,
    ScheduleCreateRequest,
    ScheduleListResponse,
    QueueStats,
    TaskInfo,
} from '@/types/automation';

// Use relative path to leverage Next.js rewrites (frontend/next.config.mjs)
// This prevents URL duplication: /api/v1/api/v1/...
const API_BASE = '/api/v1';

/**
 * List all scheduled jobs
 */
export async function listSchedules(): Promise<ScheduleListResponse> {
    const response = await fetch(`${API_BASE}/automation/schedules`);
    if (!response.ok) {
        throw new Error(`Failed to list schedules: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Create a new scheduled job
 */
export async function createSchedule(payload: ScheduleCreateRequest): Promise<Schedule> {
    const response = await fetch(`${API_BASE}/automation/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'Failed to create schedule');
    }
    return response.json();
}

/**
 * Get a specific scheduled job by ID
 */
export async function getSchedule(jobId: string): Promise<Schedule> {
    const response = await fetch(`${API_BASE}/automation/schedule/${jobId}`);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'Failed to get schedule');
    }
    return response.json();
}

/**
 * Delete a scheduled job
 */
export async function deleteSchedule(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/automation/schedule/${jobId}`, {
        method: 'DELETE',
    });
    if (!response.ok) {
        throw new Error(`Failed to delete schedule: ${response.statusText}`);
    }
}

/**
 * Pause a scheduled job
 */
export async function pauseSchedule(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/automation/schedule/${jobId}/pause`, {
        method: 'POST',
    });
    if (!response.ok) {
        throw new Error(`Failed to pause schedule: ${response.statusText}`);
    }
}

/**
 * Resume a paused scheduled job
 */
export async function resumeSchedule(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/automation/schedule/${jobId}/resume`, {
        method: 'POST',
    });
    if (!response.ok) {
        throw new Error(`Failed to resume schedule: ${response.statusText}`);
    }
}

/**
 * Update an existing scheduled job
 */
export async function updateSchedule(jobId: string, payload: ScheduleCreateRequest): Promise<Schedule> {
    const response = await fetch(`${API_BASE}/automation/schedule/${jobId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'Failed to update schedule');
    }
    return response.json();
}

/**
 * Run a scheduled job immediately (for testing)
 */
export async function runSchedule(jobId: string): Promise<{ task_id: string }> {
    const response = await fetch(`${API_BASE}/automation/schedule/${jobId}/run`, {
        method: 'POST',
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'Failed to run schedule');
    }
    return response.json();
}

/**
 * Get queue statistics from Celery
 */
export async function getQueueStats(): Promise<unknown> {
    const response = await fetch(`${API_BASE}/queue/stats`);
    if (!response.ok) {
        throw new Error(`Failed to get queue stats: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Get task info by ID
 */
export async function getTaskInfo(taskId: string): Promise<TaskInfo> {
    const response = await fetch(`${API_BASE}/queue/task/${taskId}`);
    if (!response.ok) {
        throw new Error(`Failed to get task info: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Enqueue a new agent prompt task
 */
export async function enqueueAgentPrompt(prompt: string): Promise<{ task_id: string }> {
    const response = await fetch(`${API_BASE}/queue/agent/enqueue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
    });
    if (!response.ok) {
        throw new Error(`Failed to enqueue task: ${response.statusText}`);
    }
    return response.json();
}
