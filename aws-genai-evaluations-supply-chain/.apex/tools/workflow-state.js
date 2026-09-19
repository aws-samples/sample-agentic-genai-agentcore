#!/usr/bin/env node

/**
 * workflow-state.js — Agent-driven design workflow state management.
 *
 * Called directly by the agent during workflow execution:
 *   node .apex/tools/workflow-state.js --action start    --task <taskId>
 *   node .apex/tools/workflow-state.js --action complete  --task <taskId>
 *
 * The agent reads design-handoff.json as its execution plan and calls this
 * script with explicit task IDs to update state. No hooks are involved.
 *
 * Reads and writes .apex/design-agent/design-handoff.json.
 * The extension watches this file for changes and updates the UI.
 */

const fs = require('fs');
const path = require('path');

const HANDOFF_PATH = path.join(process.cwd(), '.apex', 'design-agent', 'design-handoff.json');

function readHandoff() {
    if (!fs.existsSync(HANDOFF_PATH)) {
        console.error('design-handoff.json not found at', HANDOFF_PATH);
        process.exit(0);
    }
    const raw = fs.readFileSync(HANDOFF_PATH, 'utf8');
    return JSON.parse(raw);
}

function writeHandoff(handoff) {
    const dir = path.dirname(HANDOFF_PATH);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(HANDOFF_PATH, JSON.stringify(handoff, null, 2), 'utf8');
}

/**
 * Find a task by ID in the task tree (searches both top-level and subtasks).
 */
function findTaskById(tasks, taskId) {
    for (const task of tasks) {
        if (task.id === taskId) {
            return task;
        }
        if (task.subtasks) {
            for (const sub of task.subtasks) {
                if (sub.id === taskId) {
                    return sub;
                }
            }
        }
    }
    return null;
}

/**
 * Find the first leaf task with the given status (depth-first).
 */
function findFirstByStatus(tasks, status) {
    for (const task of tasks) {
        if (task.subtasks && task.subtasks.length > 0) {
            for (const sub of task.subtasks) {
                if (sub.status === status) {
                    return sub;
                }
            }
        } else if (task.status === status) {
            return task;
        }
    }
    return null;
}

/**
 * Find the parent task for a given subtask id.
 */
function findParent(tasks, subtaskId) {
    for (const task of tasks) {
        if (task.subtasks) {
            for (const sub of task.subtasks) {
                if (sub.id === subtaskId) {
                    return task;
                }
            }
        }
    }
    return null;
}

/**
 * Count completed leaf tasks.
 */
function countCompleted(tasks) {
    let count = 0;
    for (const task of tasks) {
        if (task.subtasks && task.subtasks.length > 0) {
            count += task.subtasks.filter(s => s.status === 'complete').length;
        } else if (task.status === 'complete') {
            count += 1;
        }
    }
    return count;
}

/**
 * Update stage info based on the active subtask id.
 */
function updateStageInfo(handoff, subtaskId) {
    const parentTask = findParent(handoff.tasks, subtaskId)
        || handoff.tasks.find(t => t.id === subtaskId);
    if (!parentTask) { return; }

    handoff.workflow.stage = parentTask.taskName;
    handoff.workflow.stageProgress.stage = parentTask.id;
    handoff.workflow.stageProgress.stageName = parentTask.taskName;

    if (parentTask.subtasks) {
        handoff.workflow.stageProgress.stageTotal = parentTask.subtasks.length;
        handoff.workflow.stageProgress.stageCompleted =
            parentTask.subtasks.filter(s => s.status === 'complete').length;
    }
}

/**
 * Collect all feedback gate task ids from the live task tree.
 */
function getFeedbackGates(tasks) {
    const gates = new Set();
    for (const task of tasks) {
        if (task.isFeedbackGate) { gates.add(task.id); }
        if (task.subtasks) {
            for (const sub of task.subtasks) {
                if (sub.isFeedbackGate) { gates.add(sub.id); }
            }
        }
    }
    return gates;
}

// ── Actions ─────────────────────────────────────────────────────

function handleStart(handoff, taskId) {
    const status = handoff.workflow.status;
    if (status === 'complete' || status === 'failed') {
        console.error(`Workflow is already ${status}, cannot start task "${taskId}".`);
        return;
    }

    const task = findTaskById(handoff.tasks, taskId);
    if (!task) {
        console.error(`Task "${taskId}" not found in the task tree.`);
        return;
    }

    if (task.status !== 'not_started') {
        console.error(`Task "${taskId}" is "${task.status}", expected "not_started".`);
        return;
    }

    task.status = 'current';

    // Mark parent as current
    const parent = findParent(handoff.tasks, taskId);
    if (parent && parent.status !== 'current') {
        parent.status = 'current';
    }

    // Feedback gate detection
    const feedbackGates = getFeedbackGates(handoff.tasks);
    if (feedbackGates.has(taskId)) {
        handoff.workflow.status = 'gathering_feedback';
    } else if (status === 'ready' || status === 'gathering_feedback') {
        handoff.workflow.status = 'in-progress';
    }

    handoff.workflow.activeTask = taskId;
    handoff.workflow.activeTaskName = task.taskName;
    updateStageInfo(handoff, taskId);
    handoff.workflow.lastUpdated = new Date().toISOString();

    writeHandoff(handoff);
}

function handleComplete(handoff, taskId) {
    const task = findTaskById(handoff.tasks, taskId);
    if (!task) {
        console.error(`Task "${taskId}" not found in the task tree.`);
        return;
    }

    if (task.status !== 'current') {
        console.error(`Task "${taskId}" is "${task.status}", expected "current".`);
        return;
    }

    task.status = 'complete';

    // Check if parent should complete
    const parent = findParent(handoff.tasks, taskId);
    if (parent) {
        const allDone = (parent.subtasks || []).every(s => s.status === 'complete');
        if (allDone) {
            parent.status = 'complete';
        }
    }

    // Recalculate progress
    const completed = countCompleted(handoff.tasks);
    const total = handoff.workflow.progress.total;
    handoff.workflow.progress.completed = completed;
    handoff.workflow.progress.percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Advance to next task
    const nextTask = findFirstByStatus(handoff.tasks, 'not_started');
    if (nextTask) {
        handoff.workflow.activeTask = nextTask.id;
        handoff.workflow.activeTaskName = nextTask.taskName;
        // If the next task is a feedback gate, pause for user input
        const feedbackGates = getFeedbackGates(handoff.tasks);
        handoff.workflow.status = feedbackGates.has(nextTask.id) ? 'gathering_feedback' : 'in-progress';
        updateStageInfo(handoff, nextTask.id);
    } else {
        updateStageInfo(handoff, taskId);
        handoff.workflow.status = 'complete';
        handoff.workflow.activeTask = 'done';
        handoff.workflow.activeTaskName = 'Workflow Complete';
    }

    handoff.workflow.lastUpdated = new Date().toISOString();

    writeHandoff(handoff);
    outputStageActions(handoff);
}

/**
 * Output [STAGE_ACTIONS] for any stage that just completed.
 * Scans the task tree for completed parent stages whose actions
 * haven't been output yet (the current task pointer has moved past them).
 */
function outputStageActions(handoff) {
    if (!handoff.stageActions) { return; }

    // Find the task just before the current pointer — that's the one that just completed.
    // Walk the tree to find the last completed leaf whose parent is also complete.
    const currentId = handoff.workflow.activeTask;
    let lastCompletedStageId = null;

    for (const stage of handoff.tasks) {
        if (stage.status !== 'complete') { continue; }
        // Check if this stage contains the subtask just before the current pointer
        if (stage.subtasks) {
            const hasCurrentOrLater = stage.subtasks.some(s => s.id === currentId || s.status === 'not_started');
            if (!hasCurrentOrLater) {
                // All subtasks in this stage are complete and the pointer has moved past
                lastCompletedStageId = stage.id;
            }
        }
    }

    if (lastCompletedStageId) {
        const actions = handoff.stageActions[lastCompletedStageId];
        if (actions && actions.postComplete && actions.postComplete.length > 0) {
            console.log(`\n[STAGE_ACTIONS:${lastCompletedStageId}]`);
            for (const action of actions.postComplete) {
                console.log(`- ${action.label}: ${action.instruction}`);
            }
            console.log(`[/STAGE_ACTIONS]`);
        }
    }
}

// ── Main ────────────────────────────────────────────────────────

const USAGE = 'Usage: node workflow-state.js --action <start|complete> --task <taskId>';

const args = process.argv.slice(2);
const actionIdx = args.indexOf('--action');
const action = actionIdx !== -1 ? args[actionIdx + 1] : null;
const taskIdx = args.indexOf('--task');
const taskId = taskIdx !== -1 ? args[taskIdx + 1] : null;

if (!action || !['start', 'complete'].includes(action)) {
    console.error(USAGE);
    process.exit(0);
}

if (!taskId) {
    console.error(USAGE);
    process.exit(0);
}

try {
    const handoff = readHandoff();
    if (action === 'start') {
        handleStart(handoff, taskId);
    } else {
        handleComplete(handoff, taskId);
    }
} catch (error) {
    console.error('workflow-state error:', error.message);
    process.exit(0);
}
