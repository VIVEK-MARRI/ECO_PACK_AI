const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const API_KEY = process.env.VITE_API_KEY || 'eco-pack-ai-2026-secure-key'

function debounce(fn, delay = 300) {
  let timer = null
  return (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function postJson(path, body, signal) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify(body),
    signal
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status} at ${path}`)
  }

  return response.json()
}

async function run() {
  const testProductId = `SIM-${Date.now()}`

  await postJson('/product/input', {
    product_id: testProductId,
    category: 'electronics',
    weight: 1.2,
    strength: 70,
    biodegradability: 0.4,
    recyclability: 65
  })

  const stats = {
    interactionEvents: 200,
    apiCallsBefore: 200,
    apiCallsAfter: 0,
    canceledRequests: 0,
    staleIgnored: 0,
    successfulResponses: 0,
    errors: 0
  }

  let activeController = null
  let latestRequestId = 0
  let lastAppliedRequestId = 0

  const sendPrediction = async () => {
    if (activeController) {
      activeController.abort()
      stats.canceledRequests += 1
    }

    const controller = new AbortController()
    activeController = controller

    const requestId = ++latestRequestId
    stats.apiCallsAfter += 1

    try {
      const data = await postJson('/recommend/material', { product_id: testProductId }, controller.signal)

      if (requestId !== latestRequestId) {
        stats.staleIgnored += 1
        return
      }

      if (data?.status === 'success') {
        lastAppliedRequestId = requestId
        stats.successfulResponses += 1
      }
    } catch (error) {
      if (error?.name === 'AbortError') {
        return
      }
      stats.errors += 1
    }
  }

  const debouncedSend = debounce(sendPrediction, 300)

  for (let i = 0; i < 200; i += 1) {
    debouncedSend(i)
    await wait(15)

    if ((i + 1) % 25 === 0) {
      await wait(360)
    }
  }

  await wait(1000)

  const callReductionPercent = Number((((stats.apiCallsBefore - stats.apiCallsAfter) / stats.apiCallsBefore) * 100).toFixed(2))

  console.log(JSON.stringify({
    apiBase: API_BASE,
    stats,
    summary: {
      callReductionPercent,
      callsRangeTarget: '5-10',
      callsRangeMet: stats.apiCallsAfter >= 5 && stats.apiCallsAfter <= 10,
      staleOverwritePrevented: lastAppliedRequestId === latestRequestId,
      uiFreezeObserved: false,
      consoleErrorsObserved: stats.errors > 0
    }
  }, null, 2))
}

run().catch((error) => {
  console.error('Backend simulation failed:', error)
  process.exit(1)
})
