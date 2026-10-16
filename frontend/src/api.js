// Relative URLs only: in dev Vite proxies /api to Flask; in prod Flask
// serves this bundle from the same origin, so no host/port hardcoding.
async function request(path, options = {}) {
  let res
  try {
    res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new Error('Cannot reach the server. Is the Flask backend running?')
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    throw new Error(`Server returned a non-JSON response (${res.status})`)
  }
  if (!res.ok) {
    throw new Error(data?.error || `Request failed (${res.status})`)
  }
  return data
}

export const health = () => request('/api/health')
export const validate = (board, goal) =>
  request('/api/validate', {
    method: 'POST',
    body: JSON.stringify({ board, goal }),
  })
export const solve = (board, goal, algorithm, limits) =>
  request('/api/solve', {
    method: 'POST',
    body: JSON.stringify({ board, goal, algorithm, limits }),
  })
export const compare = (board, goal, algorithms, limits) =>
  request('/api/compare', {
    method: 'POST',
    body: JSON.stringify({ board, goal, algorithms, limits }),
  })
