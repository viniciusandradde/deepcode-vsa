---
name: vsa-methodologies
description: IT management methodologies (ITIL, GUT, 5W2H) applied in DeepCode VSA.
---

# VSA Methodologies

This skill defines how to apply IT management frameworks within the DeepCode VSA agent.

## 📋 ITIL v4 Practices

### 1. Incident Management

- **Goal**: Restore normal service operation as quickly as possible.
- **VSA Action**: Classify request as `INCIDENTE`, identify affected CI (Configuration Item) via Zabbix/GLPI, and suggest immediate workaround.

### 2. Problem Management

- **Goal**: Identify and manage the root cause of incidents.
- **VSA Action**: Classify as `PROBLEMA`, initiate RCA (5 Whys), and correlate multiple incidents to a single root cause.

### 3. Change Management

- **Goal**: Enable successful changes by identifying risks.
- **VSA Action**: Classify as `MUDANÇA`, perform impact analysis, and create Linear issues for tracking.

## 📊 Prioritization (GUT Matrix)

Calculate the priority score using **Gravidade** (Severity), **Urgência** (Urgency), and **Tendência** (Trend).

| Level | Score | Description |
| ----- | ----- | ----------- |
| 1 | Very Low | No immediate impact / Slow evolution |
| 3 | Medium | Noticeable impact / Gradual evolution |
| 5 | Critical | Total stop / Immediate evolution |

**Formula**: `G * U * T = Score` (Max 125)

## 🔍 Structured Analysis (5W2H)

For executive reports and complex plans, follow the 5W2H pattern:

- **What**: Problem description
- **Why**: Justification
- **Where**: Affected location/system
- **When**: Timeline
- **Who**: Responsibility
- **How**: Action steps
- **How Much**: Estimated cost or impact
