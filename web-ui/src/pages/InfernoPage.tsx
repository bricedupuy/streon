import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'

interface InfernoStatus {
  is_running: boolean
  ptp_synced: boolean
  ptp_offset_ns: number | null
  ptp_delay_ns: number | null
  active_streams: number
  xrun_count: number
}

interface InfernoStream {
  id: string
  name: string
  type: 'rx' | 'tx'
  channels: number
  sample_rate: number
  is_active: boolean
  packet_count: number
}

export default function InfernoPage() {
  const [status, setStatus] = useState<InfernoStatus | null>(null)
  const [streams, setStreams] = useState<InfernoStream[]>([])
  const [config, setConfig] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editingConfig, setEditingConfig] = useState(false)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchStatus, 3000) // Refresh status every 3s
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [statusRes, streamsRes, configRes] = await Promise.all([
        apiClient.get<InfernoStatus>('/inferno/status'),
        apiClient.get<InfernoStream[]>('/inferno/streams'),
        apiClient.get<{ config: string }>('/inferno/config'),
      ])
      setStatus(statusRes.data)
      setStreams(streamsRes.data)
      setConfig(configRes.data.config)
    } catch (error) {
      console.error('Error fetching Inferno data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStatus = async () => {
    try {
      const [statusRes, streamsRes] = await Promise.all([
        apiClient.get<InfernoStatus>('/inferno/status'),
        apiClient.get<InfernoStream[]>('/inferno/streams'),
      ])
      setStatus(statusRes.data)
      setStreams(streamsRes.data)
    } catch (error) {
      console.error('Error fetching Inferno status:', error)
    }
  }

  const handleSaveConfig = async () => {
    setSaving(true)
    try {
      await apiClient.put('/inferno/config', { config })
      alert('Configuration saved successfully! Inferno will be restarted.')
      await handleRestart()
      setEditingConfig(false)
    } catch (error) {
      console.error('Error saving config:', error)
      alert('Failed to save configuration')
    } finally {
      setSaving(false)
    }
  }

  const handleRestart = async () => {
    if (!confirm('Are you sure you want to restart Inferno? This will briefly interrupt AoIP streams.')) {
      return
    }

    try {
      await apiClient.post('/inferno/restart')
      alert('Inferno is restarting...')
      setTimeout(fetchData, 5000) // Refresh after 5 seconds
    } catch (error) {
      console.error('Error restarting Inferno:', error)
      alert('Failed to restart Inferno')
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Inferno AoIP Control</h1>
        <button
          onClick={handleRestart}
          className="px-6 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg font-medium transition-colors"
        >
          Restart Inferno
        </button>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm text-gray-400 mb-2">Service Status</p>
          <div className="flex items-center gap-3">
            <div className={`w-4 h-4 rounded-full ${status?.is_running ? 'bg-green-500' : 'bg-red-500'}`} />
            <p className="text-2xl font-bold">{status?.is_running ? 'Running' : 'Stopped'}</p>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm text-gray-400 mb-2">PTP Sync</p>
          <div className="flex items-center gap-3">
            <div className={`w-4 h-4 rounded-full ${status?.ptp_synced ? 'bg-green-500' : 'bg-red-500'}`} />
            <p className="text-2xl font-bold">{status?.ptp_synced ? 'Synced' : 'Not Synced'}</p>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm text-gray-400 mb-2">Active Streams</p>
          <p className="text-3xl font-bold text-blue-500">{status?.active_streams || 0}</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <p className="text-sm text-gray-400 mb-2">XRUN Events</p>
          <p className={`text-3xl font-bold ${(status?.xrun_count || 0) > 0 ? 'text-red-500' : 'text-green-500'}`}>
            {status?.xrun_count || 0}
          </p>
        </div>
      </div>

      {/* PTP Details */}
      {status?.ptp_synced && (
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">PTP Synchronization</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-400 mb-1">Clock Offset</p>
              <p className="text-2xl font-bold font-mono">
                {status.ptp_offset_ns !== null ? `${status.ptp_offset_ns} ns` : 'N/A'}
              </p>
              <div className={`mt-2 h-2 rounded ${
                Math.abs(status.ptp_offset_ns || 0) < 1000 ? 'bg-green-500' :
                Math.abs(status.ptp_offset_ns || 0) < 10000 ? 'bg-yellow-500' :
                'bg-red-500'
              }`} />
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Path Delay</p>
              <p className="text-2xl font-bold font-mono">
                {status.ptp_delay_ns !== null ? `${status.ptp_delay_ns} ns` : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Active Streams */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">AoIP Streams</h2>

        {streams.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-gray-700">
                  <th className="pb-3 pr-4">Stream Name</th>
                  <th className="pb-3 pr-4">Type</th>
                  <th className="pb-3 pr-4">Channels</th>
                  <th className="pb-3 pr-4">Sample Rate</th>
                  <th className="pb-3 pr-4">Packet Count</th>
                  <th className="pb-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {streams.map((stream) => (
                  <tr key={stream.id} className="border-b border-gray-700">
                    <td className="py-3 pr-4 font-medium">{stream.name}</td>
                    <td className="py-3 pr-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        stream.type === 'rx' ? 'bg-blue-600' : 'bg-purple-600'
                      }`}>
                        {stream.type.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-gray-300">{stream.channels}</td>
                    <td className="py-3 pr-4 text-gray-300">{stream.sample_rate / 1000} kHz</td>
                    <td className="py-3 pr-4 font-mono text-gray-300">
                      {stream.packet_count.toLocaleString()}
                    </td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${stream.is_active ? 'bg-green-500' : 'bg-gray-500'}`} />
                        <span className="text-sm">{stream.is_active ? 'Active' : 'Inactive'}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-400">No active AoIP streams detected</p>
        )}
      </div>

      {/* Configuration Editor */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Inferno Configuration</h2>
          {!editingConfig ? (
            <button
              onClick={() => setEditingConfig(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
            >
              Edit Configuration
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={handleSaveConfig}
                disabled={saving}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save & Restart'}
              </button>
              <button
                onClick={() => {
                  setEditingConfig(false)
                  fetchData() // Reset config
                }}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {editingConfig ? (
          <textarea
            value={config}
            onChange={(e) => setConfig(e.target.value)}
            className="w-full h-96 px-4 py-3 bg-gray-900 border border-gray-600 rounded focus:border-blue-500 focus:outline-none font-mono text-sm"
            spellCheck={false}
          />
        ) : (
          <pre className="w-full h-96 overflow-auto px-4 py-3 bg-gray-900 rounded font-mono text-sm text-gray-300">
            {config}
          </pre>
        )}

        <p className="mt-4 text-sm text-gray-400">
          <strong>Note:</strong> Editing the configuration will restart Inferno and briefly interrupt AoIP streams.
          Make sure no critical broadcasts are running before making changes.
        </p>
      </div>
    </div>
  )
}
