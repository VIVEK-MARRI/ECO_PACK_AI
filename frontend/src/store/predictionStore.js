import { create } from 'zustand'

export const usePredictionStore = create((set) => ({
  prediction: null,
  loading: false,
  error: null,
  latestRequestId: 0,
  beginRequest: (requestId) =>
    set({
      loading: true,
      error: null,
      latestRequestId: requestId
    }),
  finishRequest: (requestId) =>
    set((state) => {
      if (requestId !== state.latestRequestId) return state
      return { loading: false }
    }),
  setPrediction: (prediction, requestId) =>
    set((state) => {
      if (requestId !== state.latestRequestId) return state
      return { prediction }
    }),
  setError: (error, requestId) =>
    set((state) => {
      if (requestId !== state.latestRequestId) return state
      return { error, loading: false }
    }),
  clearPredictionState: () =>
    set({
      prediction: null,
      loading: false,
      error: null,
      latestRequestId: 0
    })
}))
