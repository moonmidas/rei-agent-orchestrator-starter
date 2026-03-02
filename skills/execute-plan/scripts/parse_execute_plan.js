#!/usr/bin/env node

/**
 * Deterministic parser for /execute-plan and /xp command messages.
 *
 * Usage:
 *   node parse_execute_plan.js --text "<raw message>"
 *   node parse_execute_plan.js --file /path/to/message.txt
 *   echo "..." | node parse_execute_plan.js
 */

const fs = require('fs')

function readInput(argv) {
  const textIdx = argv.indexOf('--text')
  if (textIdx >= 0 && argv[textIdx + 1]) return argv[textIdx + 1]

  const fileIdx = argv.indexOf('--file')
  if (fileIdx >= 0 && argv[fileIdx + 1]) return fs.readFileSync(argv[fileIdx + 1], 'utf8')

  if (!process.stdin.isTTY) return fs.readFileSync(0, 'utf8')
  return ''
}

function stripMentions(input) {
  return String(input || '').replace(/<@!?\d+>/g, ' ').replace(/\u00a0/g, ' ').trim()
}

function normalizeKey(key) {
  return key
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function splitCsv(value) {
  return String(value || '')
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
}

function normalizeSkillName(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
}

function isExecutePlanSkillName(value) {
  const n = normalizeSkillName(value)
  return n === 'executeplan' || n === 'xp'
}

function applyProfileDefaults(profile) {
  const base = {
    mode: 'autopilot_sequential',
    execution: 'strict_sequential',
    task_granularity: 'medium',
    verification_gate: ['typecheck', 'build', 'targeted tests'],
    commit_strategy: 'commit_per_task',
    reporting_cadence: 'after_each_task',
    stop_conditions: 'destructive/risky/ambiguous changes',
    definition_of_done: 'all requested plan phases implemented with verification evidence',
    thread_preference: 'auto',
  }

  if (profile === 'safe') {
    base.mode = 'approval_gated'
    base.task_granularity = 'small'
  }

  if (profile === 'fast') {
    base.execution = 'allow_parallel'
  }

  if (profile === 'ship') {
    base.final_gate = 'full quality gate before final completion'
  }

  return base
}

function parseCommand(cleanText) {
  const lines = cleanText.split(/\r?\n/)
  const firstNonEmpty = lines.find((l) => l.trim()) || ''
  const first = firstNonEmpty.trim()

  const commandMatch = first.match(/^\/?(execute-plan|run-plan|xp(?:-(safe|fast|ship))?)\b/i)
  const skillInvocationMatch = first.match(/^\/?skill\s+([^\s]+)(?:\s+([\s\S]+))?$/i)

  let command = 'execute-plan'
  let profile = 'default'
  let trigger = 'direct-input'
  let firstLineRemainder = ''

  if (commandMatch) {
    command = commandMatch[1].toLowerCase()
    const suffix = commandMatch[2] ? commandMatch[2].toLowerCase() : ''
    if (command.startsWith('xp-')) profile = suffix
    trigger = command
    firstLineRemainder = first.replace(/^\/?(execute-plan|run-plan|xp(?:-(safe|fast|ship))?)\b/i, '').trim()
  } else if (skillInvocationMatch && isExecutePlanSkillName(skillInvocationMatch[1])) {
    trigger = 'skill:execute-plan'
    firstLineRemainder = String(skillInvocationMatch[2] || '').trim()
  } else if (!cleanText.trim()) {
    return { ok: false, error: 'NO_TRIGGER' }
  }

  const defaults = applyProfileDefaults(profile)

  const skipFirstLine = trigger !== 'direct-input'

  const out = {
    ok: true,
    trigger,
    profile,
    parsed: {
      ...defaults,
      plan: '',
      mode: defaults.mode,
      execution: defaults.execution,
      task_granularity: defaults.task_granularity,
      verification_gate: defaults.verification_gate,
      commit_strategy: defaults.commit_strategy,
      reporting_cadence: defaults.reporting_cadence,
      stop_conditions: defaults.stop_conditions,
      definition_of_done: defaults.definition_of_done,
      thread_preference: defaults.thread_preference,
      final_gate: defaults.final_gate || null,
      agents: [],
    },
  }

  const keyMap = new Map([
    ['plan', 'plan'],
    ['mode', 'mode'],
    ['execution', 'execution'],
    ['task granularity', 'task_granularity'],
    ['granularity', 'task_granularity'],
    ['verification gate per task', 'verification_gate'],
    ['verification gate', 'verification_gate'],
    ['verify', 'verification_gate'],
    ['commit strategy', 'commit_strategy'],
    ['commit', 'commit_strategy'],
    ['reporting cadence', 'reporting_cadence'],
    ['report', 'reporting_cadence'],
    ['stop conditions', 'stop_conditions'],
    ['stop', 'stop_conditions'],
    ['definition of done', 'definition_of_done'],
    ['done', 'definition_of_done'],
    ['thread', 'thread_preference'],
    ['thread mode', 'thread_preference'],
    ['thread preference', 'thread_preference'],
    ['thread policy', 'thread_preference'],
    ['agent', 'agents'],
    ['agents', 'agents'],
  ])

  const unstructured = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (!line.trim()) continue

    // Skip first line only when it was the command wrapper.
    if (skipFirstLine && line.trim() === first) continue

    const kv = line.match(/^([A-Za-z][A-Za-z0-9 _-]{1,80}):\s*(.*)$/)
    if (!kv) {
      unstructured.push(line)
      continue
    }

    const norm = normalizeKey(kv[1])
    const mapped = keyMap.get(norm)
    if (!mapped) {
      unstructured.push(line)
      continue
    }

    let value = String(kv[2] || '').trim()

    if (mapped === 'plan' && !value) {
      // Allow multi-line plan block after `Plan:` until next known key.
      const block = []
      for (let j = i + 1; j < lines.length; j++) {
        const nxt = lines[j]
        const nxtKv = nxt.match(/^([A-Za-z][A-Za-z0-9 _-]{1,80}):\s*(.*)$/)
        if (nxtKv && keyMap.has(normalizeKey(nxtKv[1]))) {
          break
        }
        block.push(nxt)
        i = j
      }
      value = block.join('\n').trim()
    }

    if (mapped === 'verification_gate') {
      out.parsed.verification_gate = splitCsv(value)
      continue
    }

    if (mapped === 'agents') {
      out.parsed.agents = splitCsv(value)
      continue
    }

    out.parsed[mapped] = value
  }

  // Parse inline key=value controls from full text.
  const inlineRegex = /\b([a-zA-Z][a-zA-Z_-]{1,40})=([^\s]+)/g
  let m
  while ((m = inlineRegex.exec(cleanText))) {
    const key = normalizeKey(m[1])
    const rawValue = String(m[2]).replace(/^['"]|['"]$/g, '')

    if (key === 'mode') out.parsed.mode = rawValue
    if (key === 'execution') out.parsed.execution = rawValue
    if (key === 'granularity') out.parsed.task_granularity = rawValue
    if (key === 'verify') out.parsed.verification_gate = splitCsv(rawValue)
    if (key === 'commit') out.parsed.commit_strategy = rawValue
    if (key === 'report') out.parsed.reporting_cadence = rawValue
    if (key === 'thread') out.parsed.thread_preference = rawValue
    if (key === 'agent' || key === 'agents') out.parsed.agents = splitCsv(rawValue)
  }

  if (!out.parsed.plan) {
    if (firstLineRemainder) {
      out.parsed.plan = firstLineRemainder
    } else {
      const body = unstructured.join('\n').trim()
      out.parsed.plan = body
    }
  }

  out.requires_clarification = !out.parsed.plan
  if (out.requires_clarification) {
    out.clarification_question = 'Please provide the plan text or a file path after /execute-plan (or /skill execute-plan).'
  }

  if (!Array.isArray(out.parsed.verification_gate) || out.parsed.verification_gate.length === 0) {
    out.parsed.verification_gate = defaults.verification_gate
  }

  const threadRaw = String(out.parsed.thread_preference || 'auto').toLowerCase().trim()
  if (threadRaw === 'new' || threadRaw === 'new_thread' || threadRaw === 'force_new') {
    out.parsed.thread_preference = 'new'
  } else if (threadRaw === 'current' || threadRaw === 'current_thread' || threadRaw === 'in_place') {
    out.parsed.thread_preference = 'current'
  } else {
    out.parsed.thread_preference = 'auto'
  }

  return out
}

const raw = readInput(process.argv)
const clean = stripMentions(raw)
const result = parseCommand(clean)
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
