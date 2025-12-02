import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'
import FlowMonitor from '@/components/monitoring/FlowMonitor'

interface Flow {
  id: string
  name: string
  enabled: boolean
}

interface FlowStatus {
  flow_id: string
  status: 'running' | 'stopped' | 'starting' | 'stopping' | 'error'
}

export default function MonitoringPage() {
  const [flows, setFlows] = useState<Flow[]>([])
  const [flowStatuses, setFlowStatuses] = useState<Record<string, FlowStatus>>({})
  const [selectedFlowId, setSelectedFlowId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchFlows()
    const interval = setInterval(fetchFlowStatuses, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchFlows = async () => {
    try {
      const response = await apiClient.get<Flow[]>('/flows')
      setFlows(response.data)

      // Auto-select first running Flow
      if (response.data.length > 0 && !selectedFlowId) {
        setSelectedFlowId(response.data[0].id)
      }

      await fetchFlowStatuses()
    } catch (error) {
      console.error('Error fetching flows:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchFlowStatuses = async () => {
    if (flows.length === 0) return

    const statusPromises = flows.map(flow =>
      apiClient.get<FlowStatus>(`/flows/${flow.id}/status`)
        .then(res => ({ flowId: flow.id, status: res.data }))
        .catch(() => null)
    )

    const results = await Promise.all(statusPromises)
    const statuses: Record<string, FlowStatus> = {}
    results.forEach(result => {
      if (result) {
        statuses[result.flowId] = result.status
      }
    })
    setFlowStatuses(statuses)
  }

  const runningFlows = flows.filter(f => flowStatuses[f.id]?.status === 'running')

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  if (flows.length === 0) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Monitoring</h1>
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <p className="text-gray-400 text-lg mb-4">No Flows configured</p>
          <p className="text-sm text-gray-500">Create a Flow to start monitoring</p>
        </div>
      </div>
    )
  }

  if (runningFlows.length === 0) {
    return (
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Monitoring</h1>
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <p className="text-gray-400 text-lg mb-4">No running Flows</p>
          <p className="text-sm text-gray-500">Start a Flow to see real-time monitoring</p>
        </div>
      </div>
    )
  }

  const selectedFlow = flows.find(f => f.id === selectedFlowId)

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Real-Time Monitoring</h1>

        {/* Flow Selector */}
        <div className="flex items-center gap-4">
          <label className="text-sm text-gray-400">Flow:</label>
          <select
            value={selectedFlowId || ''}
            onChange={(e) => setSelectedFlowId(e.target.value)}
            className="px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
          >
            {runningFlows.map((flow) => (
              <option key={flow.id} value={flow.id}>
                {flow.name} ({flowStatuses[flow.id]?.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Flow Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Total Flows</p>
          <p className="text-3xl font-bold">{flows.length}</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Running</p>
          <p className="text-3xl font-bold text-green-500">{runningFlows.length}</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Stopped</p>
          <p className="text-3xl font-bold text-gray-500">
            {flows.filter(f => flowStatuses[f.id]?.status === 'stopped').length}
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Errors</p>
          <p className="text-3xl font-bold text-red-500">
            {flows.filter(f => flowStatuses[f.id]?.status === 'error').length}
          </p>
        </div>
      </div>

      {/* Selected Flow Monitor */}
      {selectedFlowId && selectedFlow && (
        <div>
          <div className="mb-4">
            <h2 className="text-xl font-semibold">{selectedFlow.name}</h2>
            <p className="text-sm text-gray-400">Flow ID: {selectedFlow.id}</p>
          </div>

          <FlowMonitor flowId={selectedFlowId} />
        </div>
      )}

      {/* Grafana Link */}
      <div className="mt-8 bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-2">Advanced Monitoring</h3>
        <p className="text-gray-400 mb-4">
          For detailed metrics, historical data, and custom dashboards, access Grafana.
        </p>
        <a
          href="http://localhost:3000"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-6 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg font-medium transition-colors"
        >
          Open Grafana Dashboard →
        </a>
      </div>
    </div>
  )
}
