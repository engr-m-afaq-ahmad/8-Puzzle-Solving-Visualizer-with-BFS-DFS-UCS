import React from 'react'

const DIRECTIONS = {
  Up: '↑', Down: '↓', Left: '←', Right: '→',
}

/**
 * Pictorial 3x3 puzzle board.
 * - `state`: flat array of 9 ints (0 = blank)
 * - `goal`: optional goal used to tint correctly-placed tiles
 * - `roles`: optional map index -> 'current' | 'solution' etc.
 * - `moved`: tile number that just moved (slide highlight)
 * - `moveLabel`: arrow shown in the blank cell
 * - `onTileClick(index)`: enables interactive editing
 */
export default function Board({
  state,
  goal,
  roles = {},
  moved = null,
  moveLabel = null,
  compact = false,
  label = 'Puzzle board',
  onTileClick = null,
}) {
  if (!state || state.length !== 9) {
    return (
      <div className="board board--empty" role="img" aria-label="Empty board">
        <span>Empty board</span>
      </div>
    )
  }
  const goalIndex = new Map((goal || []).map((t, i) => [t, i]))
  return (
    <div
      className={`board ${compact ? 'board--compact' : ''}`}
      role="group"
      aria-label={label}
    >
      {state.map((tile, i) => {
        const role = roles[i]
        const inGoal = goal ? goalIndex.get(tile) === i : false
        const cls = [
          'tile',
          tile === 0 ? 'tile--blank' : '',
          inGoal ? 'tile--goal' : '',
          role ? `tile--${role}` : '',
          moved === tile ? 'tile--moved' : '',
          onTileClick ? 'tile--clickable' : '',
        ].filter(Boolean).join(' ')
        const inner = (
          <>
            {tile === 0 ? (
              moveLabel ? (
                <span className="tile__arrow" aria-hidden="true">
                  {DIRECTIONS[moveLabel] || moveLabel}
                </span>
              ) : null
            ) : (
              <span className="tile__num">{tile}</span>
            )}
          </>
        )
        const aria = tile === 0
          ? 'blank'
          : `tile ${tile}${inGoal ? ', in goal position' : ''}`
        return onTileClick ? (
          <button
            key={i}
            type="button"
            className={cls}
            onClick={() => onTileClick(i)}
            aria-label={aria}
          >
            {inner}
          </button>
        ) : (
          <div key={i} className={cls} role="img" aria-label={aria}>
            {inner}
          </div>
        )
      })}
    </div>
  )
}
