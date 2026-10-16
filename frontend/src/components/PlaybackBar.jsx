import React from 'react'

export default function PlaybackBar({
  step,
  total,
  playing,
  speed,
  onStep,
  onPlay,
  onScrub,
  onSpeed,
  disabled,
}) {
  return (
    <div className="playback" aria-label="Playback controls">
      <button
        className="btn btn--icon"
        onClick={() => onStep(-1)}
        disabled={disabled || step <= 0}
        aria-label="Previous step"
      >
        ◀
      </button>
      <button
        className="btn btn--primary btn--icon"
        onClick={onPlay}
        disabled={disabled || total === 0}
        aria-label={playing ? 'Pause' : 'Play'}
      >
        {playing ? '❚❚' : '▶'}
      </button>
      <button
        className="btn btn--icon"
        onClick={() => onStep(1)}
        disabled={disabled || step >= total - 1}
        aria-label="Next step"
      >
        ▶
      </button>
      <input
        type="range"
        min={0}
        max={Math.max(0, total - 1)}
        value={step}
        onChange={(e) => onScrub(Number(e.target.value))}
        disabled={disabled || total === 0}
        aria-label="Step position"
      />
      <span className="playback__count">
        {total === 0 ? '—' : `${step + 1} / ${total}`}
      </span>
      <select
        className="select"
        value={speed}
        onChange={(e) => onSpeed(Number(e.target.value))}
        disabled={disabled}
        aria-label="Playback speed"
      >
        <option value={600}>0.5×</option>
        <option value={300}>1×</option>
        <option value={140}>2×</option>
        <option value={60}>4×</option>
      </select>
    </div>
  )
}
