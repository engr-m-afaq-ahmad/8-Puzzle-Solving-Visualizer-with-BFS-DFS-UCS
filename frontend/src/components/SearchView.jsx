import React, { useMemo } from 'react'
import Board from './Board.jsx'

const MAX_MINIS = 10

/**
 * Search exploration player. Replays the backend's generate/expand event
 * stream: `generate` adds a node to the frontier, `expand` pops one. This
 * reconstructs the exact frontier contents at every step — no fabricated
 * data. The big board shows the state being expanded; the strip shows the
 * real frontier states as mini boards.
 */
export default function SearchView({ result, step }) {
  const { events, nodes, goal, trace_truncated: truncated } = result

  const frame = useMemo(() => {
    const frontier = new Set()
    const explored = new Set()
    let current = null
    const history = []
    const n = Math.min(step + 1, events.length)
    for (let i = 0; i < n; i++) {
      const e = events[i]
      if (e.type === 'generate') {
        frontier.add(e.id)
      } else if (e.type === 'expand') {
        frontier.delete(e.id)
        explored.add(e.id)
        current = e
      }
      history.push(e.frontier_size)
    }
    return { frontier, explored, current, history }
  }, [events, step])

  if (!events.length) {
    return <p className="hint">No exploration events to display.</p>
  }

  const curNode = frame.current ? nodes[frame.current.id] : null
  const state = frame.current ? frame.current.state : result.start
  const roles = {}
  if (frame.current) {
    // Highlight the tile that moved into the blank on the expanded state.
    const idx = state.indexOf(0)
    if (idx >= 0) roles[idx] = 'current'
  }

  const frontierIds = [...frame.frontier]
  const shown = frontierIds.slice(0, MAX_MINIS)
  const rest = frontierIds.length - shown.length
  const maxBar = Math.max(...frame.history, 1)

  return (
    <div className="searchview">
      <div className="searchview__board">
        <Board
          state={state}
          goal={goal}
          roles={roles}
          moveLabel={curNode?.move || null}
          label="Currently expanded state"
        />
        <div className="legend">
          <span><i className="swatch swatch--current" /> Being expanded</span>
          <span><i className="swatch swatch--goal" /> Tile in goal place</span>
        </div>
        <p className="hint hint--small">
          {frame.current
            ? `Expanded #${frame.current.id} · depth ${curNode?.depth} · move “${curNode?.move ?? '—'}” · frontier now ${frame.current.frontier_size}`
            : 'Seeding the search…'}
          {truncated && step >= events.length - 1 ? ' · display trace truncated' : ''}
        </p>
      </div>

      <div className="searchview__side">
        <h3 className="panel__subtitle">
          Frontier ({frame.frontier.size} state{frame.frontier.size === 1 ? '' : 's'})
        </h3>
        <div className="frontier-strip">
          {shown.length === 0 && <span className="hint">Frontier empty</span>}
          {shown.map((id) => (
            <Board key={id} state={nodes[id].state} goal={goal} compact label="Frontier state" />
          ))}
          {rest > 0 && <span className="frontier-strip__more">+{rest} more</span>}
        </div>

        <h3 className="panel__subtitle">Explored: {frame.explored.size} states</h3>
        <h3 className="panel__subtitle">Frontier size over time</h3>
        <div className="timeline" role="img" aria-label="Frontier size timeline">
          {frame.history.map((size, i) => (
            <div
              key={i}
              className={`timeline__bar ${i === step ? 'is-current' : ''}`}
              style={{ height: `${Math.max(4, (size / maxBar) * 100)}%` }}
              title={`Step ${i + 1}: frontier ${size}`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
