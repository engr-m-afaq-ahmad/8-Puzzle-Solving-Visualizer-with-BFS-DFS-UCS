import React from 'react'

const LABELS = {
  nodes_expanded: 'Nodes expanded',
  nodes_generated: 'Nodes generated',
  max_frontier_size: 'Peak frontier size',
  max_depth: 'Max depth reached',
  elapsed_ms: 'Time (ms)',
}

export default function StatsPanel({ stats, solution, algorithm, truncated }) {
  if (!stats) return null
  return (
    <section className="panel" aria-label="Statistics">
      <h2 className="panel__title">
        Statistics{algorithm ? ` · ${algorithm.toUpperCase()}` : ''}
      </h2>
      <dl className="stats">
        {Object.entries(LABELS).map(([key, label]) => (
          <div className="stats__row" key={key}>
            <dt>{label}</dt>
            <dd>
              {key === 'elapsed_ms'
                ? Number(stats[key]).toFixed(2)
                : stats[key]}
            </dd>
          </div>
        ))}
        <div className="stats__row">
          <dt>Solution moves</dt>
          <dd>{solution ? solution.length : '—'}</dd>
        </div>
        <div className="stats__row">
          <dt>Path cost</dt>
          <dd>{solution ? solution.path_cost : '—'}</dd>
        </div>
      </dl>
      {truncated && (
        <p className="hint hint--small">
          Exploration trace is truncated for display; statistics above cover
          the full search.
        </p>
      )}
    </section>
  )
}
