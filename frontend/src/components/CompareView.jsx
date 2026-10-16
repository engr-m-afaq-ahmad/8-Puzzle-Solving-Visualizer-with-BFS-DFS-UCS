import React from 'react'
import { ALGORITHM_META } from './Controls.jsx'

const ROWS = [
  { key: 'moves', label: 'Solution moves', get: (r) => (r.solved ? r.solution.length : '—') },
  { key: 'cost', label: 'Path cost', get: (r) => (r.solved ? r.solution.path_cost : '—') },
  { key: 'expanded', label: 'Nodes expanded', get: (r) => r.stats.nodes_expanded },
  { key: 'generated', label: 'Nodes generated', get: (r) => r.stats.nodes_generated },
  { key: 'frontier', label: 'Peak frontier', get: (r) => r.stats.max_frontier_size },
  { key: 'depth', label: 'Max depth', get: (r) => r.stats.max_depth },
  { key: 'time', label: 'Time (ms)', get: (r) => Number(r.stats.elapsed_ms).toFixed(2) },
]

export default function CompareView({ results, onInspect }) {
  if (!results?.length) return null
  return (
    <section className="panel" aria-label="Algorithm comparison">
      <h2 className="panel__title">Comparison</h2>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Metric</th>
              {results.map((r) => (
                <th key={r.algorithm} scope="col">
                  {ALGORITHM_META[r.algorithm]?.name || r.algorithm}
                  {!r.solvable && <span className="tag tag--bad">unsolvable</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Status</th>
              {results.map((r) => (
                <td key={r.algorithm}>
                  {r.solved
                    ? <span className="tag tag--ok">solved</span>
                    : <span className="tag tag--bad">{r.reason || 'failed'}</span>}
                </td>
              ))}
            </tr>
            {ROWS.map((row) => (
              <tr key={row.key}>
                <th scope="row">{row.label}</th>
                {results.map((r) => (
                  <td key={r.algorithm}>{row.get(r)}</td>
                ))}
              </tr>
            ))}
            <tr>
              <th scope="row">Inspect</th>
              {results.map((r) => (
                <td key={r.algorithm}>
                  <button
                    className="btn btn--small"
                    onClick={() => onInspect(r)}
                    disabled={!r.events?.length}
                  >
                    View search
                  </button>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <p className="hint hint--small">
        All values are measured during the real search run — nothing is
        estimated. BFS and UCS share unit move costs, so both return an
        optimal-length solution; DFS trades optimality for lower memory.
      </p>
    </section>
  )
}
