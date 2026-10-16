import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as api from './api.js'
import Board from './components/Board.jsx'
import Controls from './components/Controls.jsx'
import StatsPanel from './components/StatsPanel.jsx'
import PlaybackBar from './components/PlaybackBar.jsx'
import SearchView from './components/SearchView.jsx'
import CompareView from './components/CompareView.jsx'

const DEFAULT_GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]
const SAMPLE_START = [1, 2, 3, 4, 0, 6, 7, 5, 8] // optimal length 4

const adj = (a, b) => {
  const ar = Math.floor(a / 3), ac = a % 3
  const br = Math.floor(b / 3), bc = b % 3
  return Math.abs(ar - br) + Math.abs(ac - bc) === 1
}

function randomSolvable(goal) {
  // Random walk from the goal guarantees a solvable board.
  let board = [...goal]
  let blank = board.indexOf(0)
  let prev = -1
  for (let i = 0; i < 60; i++) {
    const options = [0, 1, 2, 3, 4, 5, 6, 7, 8].filter(
      (j) => j !== prev && adj(j, blank)
    )
    const pick = options[Math.floor(Math.random() * options.length)]
    board[blank] = board[pick]
    board[pick] = 0
    prev = blank
    blank = pick
  }
  return board.join(',') === goal.join(',') ? randomSolvable(goal) : board
}

export default function App() {
  const [board, setBoard] = useState(SAMPLE_START)
  const [goal, setGoal] = useState(DEFAULT_GOAL)
  const [algorithm, setAlgorithm] = useState('bfs')
  const [solvable, setSolvable] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [apiUp, setApiUp] = useState(null)

  const [result, setResult] = useState(null)
  const [compareResults, setCompareResults] = useState(null)
  const [tab, setTab] = useState('solution')

  // Playback state (shared by solution + search tabs)
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(300)
  const timer = useRef(null)

  // Blank-selection editing mode
  const [selectedBlank, setSelectedBlank] = useState(null) // 'start' | 'goal' | null

  useEffect(() => {
    api.health().then(() => setApiUp(true)).catch(() => setApiUp(false))
  }, [])

  useEffect(() => {
    let alive = true
    api.validate(board, goal)
      .then((d) => alive && setSolvable(d.solvable))
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [board, goal])

  useEffect(() => {
    setResult(null)
    setCompareResults(null)
    setStep(0)
    setPlaying(false)
  }, [board, goal])

  const totals = useMemo(() => {
    if (!result) return 0
    if (tab === 'search') return result.events?.length || 0
    return result.solved ? result.solution.length : 0
  }, [result, tab])

  useEffect(() => {
    if (!playing) { clearInterval(timer.current); return }
    timer.current = setInterval(() => {
      setStep((s) => {
        if (s >= totals - 1) { setPlaying(false); return s }
        return s + 1
      })
    }, speed)
    return () => clearInterval(timer.current)
  }, [playing, speed, totals])

  const moveTile = useCallback((which, index) => {
    const setter = which === 'start' ? setBoard : setGoal
    const current = which === 'start' ? board : goal
    const blank = current.indexOf(0)
    if (selectedBlank === which) {
      if (index === blank) { setSelectedBlank(null); return }
      if (adj(index, blank)) {
        const next = [...current]
        next[blank] = next[index]
        next[index] = 0
        setter(next)
      }
      setSelectedBlank(null)
      return
    }
    if (index === blank) { setSelectedBlank(which); return }
    if (adj(index, blank)) {
      const next = [...current]
      next[blank] = next[index]
      next[index] = 0
      setter(next)
    }
  }, [board, goal, selectedBlank])

  const runSolve = async (algo = algorithm) => {
    setBusy(true); setError(null)
    try {
      const data = await api.solve(board, goal, algo)
      setResult(data)
      setCompareResults(null)
      setTab(data.solved ? 'solution' : 'search')
      setStep(0); setPlaying(false)
      if (!data.solved && data.reason === 'unsolvable') {
        setError('This board is unsolvable to the goal — no search was run.')
      } else if (!data.solved) {
        setError(`Search stopped: ${data.reason}. Partial trace kept.`)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const runCompare = async () => {
    setBusy(true); setError(null)
    try {
      const data = await api.compare(board, goal, ['bfs', 'dfs', 'ucs'])
      setCompareResults(data.results)
      setResult(null)
      setStep(0); setPlaying(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const runValidate = async () => {
    setBusy(true); setError(null)
    try {
      const d = await api.validate(board, goal)
      setSolvable(d.solvable)
      setError(d.solvable
        ? (d.already_solved ? 'Already at the goal.' : 'Solvable — a solution exists.')
        : 'Unsolvable: inversion parity differs from the goal.')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const inspect = (r) => {
    setResult(r); setCompareResults(null); setTab('search'); setStep(0)
  }

  // ---- derived board state for playback ----
  const solutionFrame = useMemo(() => {
    if (!result?.solved || tab !== 'solution') return null
    const path = result.solution.path
    const i = Math.min(step, path.length - 1)
    const state = path[i]
    const move = i > 0 ? result.solution.moves[i - 1] : null
    let movedTile = null
    if (move) {
      const prev = path[i - 1]
      const j = state.findIndex((t, k) => t !== 0 && t !== prev[k])
      movedTile = j >= 0 ? state[j] : null
    }
    return { state, move, movedTile, index: i, total: path.length }
  }, [result, step, tab])

  const stepDelta = (d) => setStep((s) => Math.max(0, Math.min(totals - 1, s + d)))

  return (
    <div className="app">
      <header className="header">
        <h1>8-Puzzle AI Visualizer</h1>
        <p className="header__sub">
          BFS · DFS · UCS search exploration, solvability checks and real statistics
          {'  '}
          <span className={`dot ${apiUp === null ? '' : apiUp ? 'dot--ok' : 'dot--bad'}`} />
          {apiUp === null ? ' connecting…' : apiUp ? ' API connected' : ' API offline'}
        </p>
      </header>

      {error && (
        <div className="banner" role="alert">
          {error}
          <button className="banner__close" onClick={() => setError(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      <div className="layout">
        <div className="layout__main">
          <section className="panel" aria-label="Boards">
            <h2 className="panel__title">Start board {selectedBlank === 'start' && <span className="tag">pick a tile</span>}</h2>
            <div className="boards">
              <div>
                <Board
                  state={board}
                  goal={goal}
                  label="Start board"
                  onTileClick={(i) => moveTile('start', i)}
                />
                <div className="board-caption">Click a tile beside the blank to slide it</div>
              </div>
              <div className="boards__arrow" aria-hidden="true">→</div>
              <div>
                <h2 className="panel__title">Goal {selectedBlank === 'goal' && <span className="tag">pick a tile</span>}</h2>
                <Board
                  state={goal}
                  label="Goal board"
                  onTileClick={(i) => moveTile('goal', i)}
                />
                <div className="board-caption">Goal is editable too — same rules</div>
              </div>
            </div>
          </section>

          <nav className="tabs" aria-label="Views">
            {[['solution', 'Solution'], ['search', 'Search exploration'], ['compare', 'Compare']].map(([id, label]) => (
              <button
                key={id}
                className={`tab ${tab === id ? 'is-active' : ''}`}
                onClick={() => { setTab(id); setStep(0); setPlaying(false) }}
                disabled={
                  (id !== 'compare' && !result) ||
                  (id === 'compare' && !compareResults)
                }
              >
                {label}
              </button>
            ))}
          </nav>

          {tab === 'solution' && solutionFrame && (
            <section className="panel" aria-label="Solution playback">
              <h2 className="panel__title">
                Solution · {algorithm.toUpperCase()} · move {solutionFrame.index} of {solutionFrame.total - 1}
              </h2>
              <div className="solution">
                <Board
                  state={solutionFrame.state}
                  goal={goal}
                  roles={solutionFrame.index === solutionFrame.total - 1
                    ? Object.fromEntries([0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => [i, 'solution']))
                    : {}}
                  moved={solutionFrame.movedTile}
                  moveLabel={solutionFrame.move}
                  label="Solution step"
                />
                <ol className="moves" aria-label="Move list">
                  {result.solution.moves.map((m, i) => (
                    <li key={i} className={i === solutionFrame.index - 1 ? 'is-current' : ''}>
                      <button className="btn btn--small" onClick={() => { setTab('solution'); setStep(i + 1) }}>
                        {i + 1}. {m}
                      </button>
                    </li>
                  ))}
                </ol>
              </div>
            </section>
          )}

          {tab === 'search' && result && (
            <section className="panel" aria-label="Search exploration">
              <h2 className="panel__title">Search exploration · {result.algorithm.toUpperCase()}</h2>
              <SearchView result={result} step={step} />
            </section>
          )}

          {tab === 'search' && result && (
            <PlaybackBar
              step={step}
              total={totals}
              playing={playing}
              speed={speed}
              onStep={stepDelta}
              onPlay={() => {
                if (step >= totals - 1) setStep(0)
                setPlaying((p) => !p)
              }}
              onScrub={setStep}
              onSpeed={setSpeed}
              disabled={busy}
            />
          )}

          {tab === 'solution' && solutionFrame && (
            <PlaybackBar
              step={step}
              total={totals}
              playing={playing}
              speed={speed}
              onStep={stepDelta}
              onPlay={() => {
                if (step >= totals - 1) setStep(0)
                setPlaying((p) => !p)
              }}
              onScrub={setStep}
              onSpeed={setSpeed}
              disabled={busy}
            />
          )}

          {compareResults && (
            <CompareView results={compareResults} onInspect={inspect} />
          )}
        </div>

        <aside className="layout__side">
          <Controls
            algorithm={algorithm}
            onAlgorithm={setAlgorithm}
            onSolve={() => runSolve()}
            onCompare={runCompare}
            onValidate={runValidate}
            onReset={() => setBoard(SAMPLE_START)}
            onShuffle={() => setBoard(randomSolvable(goal))}
            onClear={() => { setBoard([...goal]); setSelectedBlank(null) }}
            busy={busy}
            solvable={solvable}
            board={board}
          />
          {result && (
            <StatsPanel
              stats={result.stats}
              solution={result.solved ? result.solution : null}
              algorithm={result.algorithm}
              truncated={result.trace_truncated}
            />
          )}
        </aside>
      </div>

      <footer className="footer">
        Flask API + React/Vite · BFS, DFS and UCS with parity solvability · same-origin production build
      </footer>
    </div>
  )
}
