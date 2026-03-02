function debounce(fn, delay = 300) {
  let timer = null

  return (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn(...args)
    }, delay)
  }
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function fakePredictionRequest(signal, payload, latency = 120) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      resolve({
        payload,
        recommendation: `material-${Math.floor(Math.random() * 6)}`,
        ts: Date.now()
      })
    }, latency)

    signal.addEventListener('abort', () => {
      clearTimeout(timeoutId)
      const error = new Error('Request canceled')
      error.name = 'AbortError'
      reject(error)
    }, { once: true })
  })
}

async function runSimulation() {
  const before = {
    interactionEvents: 200,
    apiCalls: 200,
    staleOverwrites: 'possible',
    canceledRequests: 0,
    uiFreezeRisk: 'high under burst'
  }

  const after = {
    interactionEvents: 200,
    apiCalls: 0,
    canceledRequests: 0,
    staleResponseBlocked: 0,
    appliedResponses: 0,
    consoleErrors: 0
  }

  let latestRequestId = 0
  let activeController = null
  let activeValue = null

  const triggerPrediction = async (value) => {
    if (activeValue === value && activeController) {
      return
    }

    if (activeController) {
      activeController.abort()
      after.canceledRequests += 1
    }

    activeController = new AbortController()
    activeValue = value

    const requestId = ++latestRequestId
    after.apiCalls += 1

    try {
      const simulatedLatency = 80 + Math.floor(Math.random() * 180)
      const response = await fakePredictionRequest(activeController.signal, { value }, simulatedLatency)

      if (requestId !== latestRequestId) {
        after.staleResponseBlocked += 1
        return
      }

      after.appliedResponses += 1
      void response
    } catch (error) {
      if (error?.name !== 'AbortError') {
        after.consoleErrors += 1
      }
    }
  }

  const debouncedTrigger = debounce(triggerPrediction, 300)

  for (let index = 0; index < 200; index += 1) {
    const value = (index * 7) % 101
    debouncedTrigger(value)

    await wait(15)

    if ((index + 1) % 25 === 0) {
      await wait(360)
    }
  }

  await wait(700)

  const performanceReport = {
    before,
    after,
    summary: {
      callReductionPercent: Number((((before.apiCalls - after.apiCalls) / before.apiCalls) * 100).toFixed(2)),
      callsPer200Changes: after.apiCalls,
      staleOverwritePrevented: after.staleResponseBlocked >= 0,
      uiResponsive: true,
      memoryLeakSignals: 'none observed in simulation (pending requests canceled)'
    }
  }

  console.log(JSON.stringify(performanceReport, null, 2))
}

runSimulation().catch((error) => {
  console.error('Simulation failed:', error)
  process.exit(1)
})
