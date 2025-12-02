import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'
import FlowEditor from '@/components/flows/FlowEditor'

interface Flow {
  id: string
  name: string
  enabled: boolean
}

interface FlowStatus {
  flow_id: string
  status: 'running' | 'stopped' | 'starting' | 'stopping' | 'error'
  liquidsoap_pid: number | null
  ffmpeg_pids: number[]
  uptime_seconds: number | null
  last_error: string | null
}

export default function FlowsPage() {
  const [flows, setFlows] = useState<Flow[]>([])
  const [flowStatuses, setFlowStatuses] = useState<Record<string, FlowStatus>>({})
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)
  const [editingFlowId, setEditingFlowId] = useState<string | undefined>(undefined)

  useEffect(() => {
    fetchFlows()
    const interval = setInterval(fetchStatuses, 3000) // Refresh status every 3s
    return () => clearInterval(interval)
  }, [flows])

  const fetchFlows = async () => {
    try {
      const response = await apiClient.get<Flow[]>('/flows')
      setFlows(response.data)
      if (response.data.length > 0) {
        fetchStatuses()
      }
    } catch (error) {
      console.error('Error fetching flows:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStatuses = async () => {
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

  const handleStartFlow = async (flowId: string) => {
    try {
      await apiClient.post(`/flows/${flowId}/start`)
      await fetchStatuses()
    } catch (error) {
      console.error('Error starting flow:', error)
      alert('Failed to start flow')
    }
  }

  const handleStopFlow = async (flowId: string) => {
    try {
      await apiClient.post(`/flows/${flowId}/stop`)
      await fetchStatuses()
    } catch (error) {
      console.error('Error stopping flow:', error)
      alert('Failed to stop flow')
    }
  }

  const handleRestartFlow = async (flowId: string) => {
    try {
      await apiClient.post(`/flows/${flowId}/restart`)
      await fetchStatuses()
    } catch (error) {
      console.error('Error restarting flow:', error)
      alert('Failed to restart flow')
    }
  }

  const handleDeleteFlow = async (flowId: string) => {
    if (!confirm('Are you sure you want to delete this flow?')) return

    try {
      await apiClient.delete(`/flows/${flowId}`)
      await fetchFlows()
    } catch (error) {
      console.error('Error deleting flow:', error)
      alert('Failed to delete flow')
    }
  }

  const handleCreateFlow = () => {
    setEditingFlowId(undefined)
    setShowEditor(true)
  }

  const handleEditorSave = async () => {
    setShowEditor(false)
    setEditingFlowId(undefined)
    await fetchFlows()
  }

  const handleEditorCancel = () => {
    setShowEditor(false)
    setEditingFlowId(undefined)
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  if (showEditor) {
    return (
      <div className="p-8">
        <FlowEditor
          flowId={editingFlowId}
          onSave={handleEditorSave}
          onCancel={handleEditorCancel}
        />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Flows</h1>
        <button
          onClick={handleCreateFlow}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
        >
          ➕ Create Flow
        </button>
      </div>

      {flows.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <p className="text-gray-400 text-lg mb-4">No flows configured</p>
          <button
            onClick={handleCreateFlow}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            Create Your First Flow
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {flows.map((flow) => (
            <FlowCard
              key={flow.id}
              flow={flow}
              status={flowStatuses[flow.id]}
              onStart={handleStartFlow}
              onStop={handleStopFlow}
              onRestart={handleRestartFlow}
              onDelete={handleDeleteFlow}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function FlowCard({
  flow,
  status,
  onStart,
  onStop,
  onRestart,
  onDelete,
}: {
  flow: Flow
  status?: FlowStatus
  onStart: (id: string) => void
  onStop: (id: string) => void
  onRestart: (id: string) => void
  onDelete: (id: string) => void
}) {
  const getStatusColor = () => {
    if (!status) return 'bg-gray-500'
    switch (status.status) {
      case 'running':
        return 'bg-green-500'
      case 'stopped':
        return 'bg-gray-500'
      case 'starting':
      case 'stopping':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const formatUptime = (seconds: number | null) => {
    if (!seconds) return 'N/A'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const isRunning = status?.status === 'running'

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold mb-1">{flow.name}</h3>
          <p className="text-sm text-gray-400 font-mono">{flow.id}</p>
        </div>
        <div className={`w-4 h-4 rounded-full ${getStatusColor()}`} />
      </div>

      {status && (
        <div className="space-y-2 text-sm mb-4">
          <div className="flex justify-between">
            <span className="text-gray-400">Status:</span>
            <span className="capitalize">{status.status}</span>
          </div>
          {isRunning && (
            <>
              <div className="flex justify-between">
                <span className="text-gray-400">Uptime:</span>
                <span>{formatUptime(status.uptime_seconds)}</span>
              </div>
              {status.liquidsoap_pid && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Liquidsoap PID:</span>
                  <span className="font-mono">{status.liquidsoap_pid}</span>
                </div>
              )}
              {status.ffmpeg_pids.length > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">FFmpeg PIDs:</span>
                  <span className="font-mono">{status.ffmpeg_pids.join(', ')}</span>
                </div>
              )}
            </>
          )}
          {status.last_error && (
            <div className="mt-2 p-2 bg-red-900/30 rounded text-red-400 text-xs">
              {status.last_error}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {!isRunning ? (
          <button
            onClick={() => onStart(flow.id)}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors text-sm font-medium"
          >
            ▶️ Start
          </button>
        ) : (
          <>
            <button
              onClick={() => onStop(flow.id)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors text-sm font-medium"
            >
              ⏹️ Stop
            </button>
            <button
              onClick={() => onRestart(flow.id)}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded transition-colors text-sm font-medium"
            >
              🔄 Restart
            </button>
          </>
        )}
        <button
          onClick={() => onDelete(flow.id)}
          disabled={isRunning}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          🗑️ Delete
        </button>
      </div>
    </div>
  )
}
