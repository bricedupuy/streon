import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'

interface NetworkInterface {
  name: string
  type: 'ethernet' | 'wifi' | 'loopback'
  state: 'up' | 'down' | 'unknown'
  ip_address: string | null
  netmask: string | null
  gateway: string | null
  mac_address: string | null
  mtu: number
  speed_mbps: number | null
  is_dhcp: boolean
}

interface Route {
  destination: string
  gateway: string
  interface: string
  metric: number
}

export default function NetworkPage() {
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([])
  const [routes, setRoutes] = useState<Route[]>([])
  const [loading, setLoading] = useState(true)
  const [editingInterface, setEditingInterface] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // Form state for editing
  const [formData, setFormData] = useState({
    isDhcp: true,
    ipAddress: '',
    netmask: '255.255.255.0',
    gateway: '',
    mtu: 1500,
  })

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [interfacesRes, routesRes] = await Promise.all([
        apiClient.get<NetworkInterface[]>('/network/interfaces'),
        apiClient.get<Route[]>('/network/routes'),
      ])
      setInterfaces(interfacesRes.data)
      setRoutes(routesRes.data)
    } catch (error) {
      console.error('Error fetching network data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleEditInterface = (iface: NetworkInterface) => {
    setEditingInterface(iface.name)
    setFormData({
      isDhcp: iface.is_dhcp,
      ipAddress: iface.ip_address || '',
      netmask: iface.netmask || '255.255.255.0',
      gateway: iface.gateway || '',
      mtu: iface.mtu,
    })
  }

  const handleSaveInterface = async () => {
    if (!editingInterface) return

    setSaving(true)
    try {
      await apiClient.put(`/network/interfaces/${editingInterface}`, {
        is_dhcp: formData.isDhcp,
        ip_address: formData.isDhcp ? null : formData.ipAddress,
        netmask: formData.isDhcp ? null : formData.netmask,
        gateway: formData.isDhcp ? null : formData.gateway,
        mtu: formData.mtu,
      })
      alert('Network configuration saved! Changes will apply after network restart.')
      await fetchData()
      setEditingInterface(null)
    } catch (error) {
      console.error('Error saving interface:', error)
      alert('Failed to save network configuration')
    } finally {
      setSaving(false)
    }
  }

  const handleApplyChanges = async () => {
    if (!confirm('Apply network changes? This will restart networking and may interrupt connections.')) {
      return
    }

    try {
      await apiClient.post('/network/apply')
      alert('Network changes applied successfully!')
      setTimeout(fetchData, 3000) // Refresh after 3 seconds
    } catch (error) {
      console.error('Error applying network changes:', error)
      alert('Failed to apply network changes')
    }
  }

  const handleToggleInterface = async (ifaceName: string, currentState: string) => {
    const newState = currentState === 'up' ? 'down' : 'up'

    if (!confirm(`${newState === 'up' ? 'Enable' : 'Disable'} interface ${ifaceName}?`)) {
      return
    }

    try {
      await apiClient.post(`/network/interfaces/${ifaceName}/${newState}`)
      await fetchData()
    } catch (error) {
      console.error(`Error toggling interface:`, error)
      alert(`Failed to ${newState === 'up' ? 'enable' : 'disable'} interface`)
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Network Configuration</h1>
        <button
          onClick={handleApplyChanges}
          className="px-6 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg font-medium transition-colors"
        >
          Apply Network Changes
        </button>
      </div>

      {/* Warning Notice */}
      <div className="bg-yellow-900/30 border border-yellow-600 rounded-lg p-4 mb-6">
        <p className="text-yellow-400 font-medium mb-2">⚠️ Network Configuration Warning</p>
        <p className="text-sm text-yellow-300">
          Changing network settings may interrupt your connection to this interface.
          For Dante networks, ensure you have a separate control network or physical access to the system.
        </p>
      </div>

      {/* Network Interfaces */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Network Interfaces</h2>

        <div className="space-y-4">
          {interfaces.map((iface) => (
            <div key={iface.name} className="bg-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4">
                  <div>
                    <h3 className="text-lg font-semibold">{iface.name}</h3>
                    <p className="text-sm text-gray-400">
                      {iface.type.charAt(0).toUpperCase() + iface.type.slice(1)}
                      {iface.mac_address && ` • ${iface.mac_address}`}
                    </p>
                  </div>
                  <div className={`px-3 py-1 rounded text-sm font-medium ${
                    iface.state === 'up' ? 'bg-green-600' : 'bg-gray-600'
                  }`}>
                    {iface.state.toUpperCase()}
                  </div>
                  {iface.is_dhcp && (
                    <div className="px-3 py-1 bg-blue-600 rounded text-sm font-medium">
                      DHCP
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  {iface.type !== 'loopback' && (
                    <>
                      <button
                        onClick={() => handleToggleInterface(iface.name, iface.state)}
                        className={`px-3 py-1 rounded text-sm transition-colors ${
                          iface.state === 'up'
                            ? 'bg-gray-600 hover:bg-gray-700'
                            : 'bg-green-600 hover:bg-green-700'
                        }`}
                      >
                        {iface.state === 'up' ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        onClick={() => handleEditInterface(iface)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                      >
                        Configure
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Interface Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-400 mb-1">IP Address</p>
                  <p className="font-mono">{iface.ip_address || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-400 mb-1">Netmask</p>
                  <p className="font-mono">{iface.netmask || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-400 mb-1">Gateway</p>
                  <p className="font-mono">{iface.gateway || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-400 mb-1">MTU</p>
                  <p className="font-mono">{iface.mtu}</p>
                </div>
                {iface.speed_mbps && (
                  <div>
                    <p className="text-gray-400 mb-1">Speed</p>
                    <p className="font-mono">{iface.speed_mbps} Mbps</p>
                  </div>
                )}
              </div>

              {/* Edit Form */}
              {editingInterface === iface.name && (
                <div className="mt-4 pt-4 border-t border-gray-600">
                  <h4 className="font-medium mb-4">Configure {iface.name}</h4>

                  <div className="space-y-4">
                    {/* DHCP Toggle */}
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        id="dhcp"
                        checked={formData.isDhcp}
                        onChange={(e) => setFormData({ ...formData, isDhcp: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <label htmlFor="dhcp" className="text-sm font-medium">
                        Use DHCP (automatic configuration)
                      </label>
                    </div>

                    {/* Static IP Configuration */}
                    {!formData.isDhcp && (
                      <>
                        <div>
                          <label className="block text-sm font-medium mb-2">IP Address *</label>
                          <input
                            type="text"
                            value={formData.ipAddress}
                            onChange={(e) => setFormData({ ...formData, ipAddress: e.target.value })}
                            placeholder="192.168.1.100"
                            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none font-mono"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2">Netmask *</label>
                          <input
                            type="text"
                            value={formData.netmask}
                            onChange={(e) => setFormData({ ...formData, netmask: e.target.value })}
                            placeholder="255.255.255.0"
                            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none font-mono"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2">Gateway (optional)</label>
                          <input
                            type="text"
                            value={formData.gateway}
                            onChange={(e) => setFormData({ ...formData, gateway: e.target.value })}
                            placeholder="192.168.1.1"
                            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none font-mono"
                          />
                        </div>
                      </>
                    )}

                    {/* MTU */}
                    <div>
                      <label className="block text-sm font-medium mb-2">MTU</label>
                      <input
                        type="number"
                        value={formData.mtu}
                        onChange={(e) => setFormData({ ...formData, mtu: parseInt(e.target.value) })}
                        min="576"
                        max="9000"
                        className="w-full px-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none font-mono"
                      />
                      <p className="text-xs text-gray-400 mt-1">
                        Standard: 1500, Jumbo frames: 9000 (for Dante networks)
                      </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveInterface}
                        disabled={saving || (!formData.isDhcp && !formData.ipAddress)}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {saving ? 'Saving...' : 'Save Configuration'}
                      </button>
                      <button
                        onClick={() => setEditingInterface(null)}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Routing Table */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Routing Table</h2>

        {routes.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-gray-700">
                  <th className="pb-3 pr-4">Destination</th>
                  <th className="pb-3 pr-4">Gateway</th>
                  <th className="pb-3 pr-4">Interface</th>
                  <th className="pb-3">Metric</th>
                </tr>
              </thead>
              <tbody>
                {routes.map((route, idx) => (
                  <tr key={idx} className="border-b border-gray-700">
                    <td className="py-3 pr-4 font-mono text-sm">{route.destination}</td>
                    <td className="py-3 pr-4 font-mono text-sm">{route.gateway}</td>
                    <td className="py-3 pr-4 font-medium">{route.interface}</td>
                    <td className="py-3 font-mono text-sm">{route.metric}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-400">No routes configured</p>
        )}
      </div>

      {/* Best Practices for Dante */}
      <div className="mt-8 bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Dante Network Best Practices</h3>
        <div className="space-y-3 text-sm text-gray-300">
          <div className="flex gap-3">
            <span className="text-blue-400">✓</span>
            <p><strong>Separate Networks:</strong> Use dedicated network interface for Dante traffic (e.g., eth1 for Dante, eth0 for control)</p>
          </div>
          <div className="flex gap-3">
            <span className="text-blue-400">✓</span>
            <p><strong>Static IP:</strong> Configure Dante interface with static IP in 169.254.x.x range or your network's subnet</p>
          </div>
          <div className="flex gap-3">
            <span className="text-blue-400">✓</span>
            <p><strong>Jumbo Frames:</strong> Set MTU to 9000 on Dante interface for better performance (requires switch support)</p>
          </div>
          <div className="flex gap-3">
            <span className="text-blue-400">✓</span>
            <p><strong>QoS/DSCP:</strong> Ensure network switches support DSCP/QoS for audio traffic prioritization</p>
          </div>
          <div className="flex gap-3">
            <span className="text-blue-400">✓</span>
            <p><strong>PTP-Capable Switch:</strong> Use managed switches with PTPv2 support for clock synchronization</p>
          </div>
        </div>
      </div>
    </div>
  )
}
