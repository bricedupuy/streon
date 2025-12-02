import { useEffect, useState } from 'react'
import { apiClient } from '@/api/client'

interface SystemHealth {
  controller_up: boolean
  inferno_up: boolean | null
  ptp_synced: boolean | null
  active_flows: number
  cpu_usage_percent: number
  memory_usage_percent: number
  disk_usage_percent: number
}

export default function Dashboard() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const fetchHealth = async () => {
    try {
      const response = await apiClient.get<SystemHealth>('/system/health')
      setHealth(response.data)
    } catch (error) {
      console.error('Error fetching health:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatusCard
          title="Controller"
          status={health?.controller_up ? 'online' : 'offline'}
          value={health?.controller_up ? 'Running' : 'Stopped'}
        />
        <StatusCard
          title="Active Flows"
          status="info"
          value={health?.active_flows.toString() || '0'}
        />
        <StatusCard
          title="Inferno AoIP"
          status={health?.inferno_up ? 'online' : 'offline'}
          value={health?.inferno_up ? 'Connected' : 'Disconnected'}
        />
        <StatusCard
          title="PTP Sync"
          status={health?.ptp_synced ? 'online' : 'offline'}
          value={health?.ptp_synced ? 'Synced' : 'Not Synced'}
        />
      </div>

      {/* Resource Usage */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">System Resources</h2>
        <div className="space-y-4">
          <ResourceBar
            label="CPU Usage"
            value={health?.cpu_usage_percent || 0}
          />
          <ResourceBar
            label="Memory Usage"
            value={health?.memory_usage_percent || 0}
          />
          <ResourceBar
            label="Disk Usage"
            value={health?.disk_usage_percent || 0}
          />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QuickActionButton href="/flows" label="Manage Flows" />
          <QuickActionButton href="/devices" label="Scan Devices" />
          <QuickActionButton href="/stereotool" label="Upload Presets" />
          <QuickActionButton href="/monitoring" label="View Metrics" />
        </div>
      </div>
    </div>
  )
}

function StatusCard({ title, status, value }: { title: string; status: string; value: string }) {
  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-red-500',
    info: 'bg-blue-500',
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        <div className={`w-3 h-3 rounded-full ${statusColors[status as keyof typeof statusColors] || 'bg-gray-500'}`} />
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}

function ResourceBar({ label, value }: { label: string; value: number }) {
  const getColor = (val: number) => {
    if (val >= 90) return 'bg-red-500'
    if (val >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-sm font-medium">{value.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${getColor(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

function QuickActionButton({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg text-center transition-colors"
    >
      {label}
    </a>
  )
}
