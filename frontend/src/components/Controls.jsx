import React from 'react'

const ALGOS = [
  { id: 'bfs', name: 'BFS', desc: 'Breadth-first — optimal, explores level by level' },
  { id: 'dfs', name: 'DFS', desc: 'Depth-first — fast, not optimal' },
  { id: 'ucs', name: 'UCS', desc: 'Uniform-cost — optimal for unit move costs' },
]

export const ALGORITHM_META = Object.fromEntries(ALGOS.map((a) => [a.id, a]))

export default function Controls({
  algorithm,
  onAlgorithm,
  onSolve,
  onCompare,
  onValidate,
  onReset,
  onShuffle,
  onClear,
  busy,
  solvable,
  board,
}) {
  return (
    <section className="panel controls" aria-label="Search controls">
      <h2 className="panel__title">Algorithm</h2>
      <div className="algo-group" role="radiogroup" aria-label="Choose algorithm">
        {ALGOS.map((a) => (
          <button
            key={a.id}
            role="radio"
            aria-checked={algorithm === a.id}
            className={`btn btn--algo ${algorithm === a.id ? 'is-active' : ''}`}
            onClick={() => onAlgorithm(a.id)}
            disabled={busy}
            title={a.desc}
          >
            {a.name}
          </button>
        ))}
      </div>

      <h2 className="panel__title">Puzzle</h2>
      <div className="btn-row">
        <button className="btn btn--primary" onClick={onSolve} disabled={busy}>
          {busy ? 'Solving…' : 'Solve'}
        </button>
        <button className="btn" onClick={onCompare} disabled={busy}>
          Compare all
        </button>
        <button className="btn" onClick={onValidate} disabled={busy}>
          Check solvable
        </button>
      </div>
      <div className="btn-row">
        <button className="btn" onClick={onShuffle} disabled={busy}>
          Random solvable
        </button>
        <button className="btn" onClick={onReset} disabled={busy}>
          Reset start
        </button>
        <button className="btn" onClick={onClear} disabled={busy}>
          Start = goal
        </button>
      </div>

      <p className="hint">
        Click a tile next to the blank to move it, or click the blank and then
        an adjacent tile.{' '}
        {solvable === true && <span className="tag tag--ok">Solvable</span>}
        {solvable === false && (
          <span className="tag tag--bad">Unsolvable to goal</span>
        )}
      </p>
      {board && solvable === false && (
        <p className="hint hint--small">
          Unsolvable boards have an odd inversion parity relative to the goal;
          no sequence of legal moves can reach it.
        </p>
      )}
    </section>
  )
}
