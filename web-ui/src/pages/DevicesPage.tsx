import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'

interface AudioDevice {
  id: string
  type: string
  device_name: string
  friendly_name: string | null
  channels: number
  sample_rate: number
  is_available: boolean
  in_use_by: string | null
  last_seen: string
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<AudioDevice[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    fetchDevices()
  }, [])

  const fetchDevices = async () => {
    try {
      const response = await apiClient.get<AudioDevice[]>('/devices')
      setDevices(response.data)
    } catch (error) {
      console.error('Error fetching devices:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      await apiClient.get('/devices/scan')
      await fetchDevices()
    } catch (error) {
      console.error('Error scanning devices:', error)
      alert('Failed to scan devices')
    } finally {
      setScanning(false)
    }
  }

  const handleUpdateFriendlyName = async (deviceId: string, friendlyName: string) => {
    try {
      await apiClient.put(`/devices/${deviceId}`, { friendly_name: friendlyName })
      await fetchDevices()
    } catch (error) {
      console.error('Error updating device:', error)
      alert('Failed to update device')
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  const groupedDevices = devices.reduce((acc, device) => {
    const type = device.type
    if (!acc[type]) acc[type] = []
    acc[type].push(device)
    return acc
  }, {} as Record<string, AudioDevice[]>)

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Audio Devices</h1>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {scanning ? 'Scanning...' : '🔍 Scan Devices'}
        </button>
      </div>

      {devices.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <p className="text-gray-400 text-lg mb-4">No devices found</p>
          <button
            onClick={handleScan}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            Scan for Devices
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedDevices).map(([type, devicesOfType]) => (
            <div key={type}>
              <h2 className="text-xl font-semibold mb-3 capitalize">
                {type.replace('_', ' ')} Devices ({devicesOfType.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {devicesOfType.map((device) => (
                  <DeviceCard
                    key={device.id}
                    device={device}
                    onUpdateFriendlyName={handleUpdateFriendlyName}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function DeviceCard({
  device,
  onUpdateFriendlyName,
}: {
  device: AudioDevice
  onUpdateFriendlyName: (deviceId: string, friendlyName: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [friendlyName, setFriendlyName] = useState(device.friendly_name || device.device_name)

  const handleSubmit = () => {
    onUpdateFriendlyName(device.id, friendlyName)
    setEditing(false)
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          {editing ? (
            <div className="space-y-2">
              <input
                type="text"
                value={friendlyName}
                onChange={(e) => setFriendlyName(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                autoFocus
              />
              <div className="flex space-x-2">
                <button
                  onClick={handleSubmit}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setEditing(false)
                    setFriendlyName(device.friendly_name || device.device_name)
                  }}
                  className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <h3 className="font-semibold text-lg mb-1">
                {device.friendly_name || device.device_name}
              </h3>
              <button
                onClick={() => setEditing(true)}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                Edit name
              </button>
            </>
          )}
        </div>

        <div className={`px-2 py-1 rounded text-xs ${
          device.is_available ? 'bg-green-600' : 'bg-red-600'
        }`}>
          {device.is_available ? 'Available' : 'Unavailable'}
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Device:</span>
          <span className="font-mono">{device.device_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Type:</span>
          <span className="capitalize">{device.type.replace('_', ' ')}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Channels:</span>
          <span>{device.channels}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Sample Rate:</span>
          <span>{device.sample_rate} Hz</span>
        </div>
        {device.in_use_by && (
          <div className="flex justify-between">
            <span className="text-gray-400">In Use By:</span>
            <span className="text-yellow-400">{device.in_use_by}</span>
          </div>
        )}
      </div>
    </div>
  )
}
