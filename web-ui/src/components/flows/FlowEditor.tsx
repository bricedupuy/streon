import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'

interface FlowEditorProps {
  flowId?: string
  onSave: () => void
  onCancel: () => void
}

interface Device {
  id: string
  type: string
  device_name: string
  friendly_name: string | null
  channels: number
  sample_rate: number
  is_available: boolean
}

interface StereoToolPreset {
  id: string
  name: string
  filename: string
}

export default function FlowEditor({ flowId, onSave, onCancel }: FlowEditorProps) {
  const [devices, setDevices] = useState<Device[]>([])
  const [presets, setPresets] = useState<StereoToolPreset[]>([])
  const [loading, setLoading] = useState(false)

  // Form state
  const [flowName, setFlowName] = useState('')
  const [enabled, setEnabled] = useState(true)

  // Input configuration
  const [inputType, setInputType] = useState<string>('alsa')
  const [inputDevice, setInputDevice] = useState<string>('')
  const [inputChannels, setInputChannels] = useState<number>(2)
  const [inputSampleRate, setInputSampleRate] = useState<number>(48000)

  // Processing configuration
  const [stereoToolEnabled, setStereoToolEnabled] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<string>('')
  const [silenceThreshold, setSilenceThreshold] = useState<number>(-50)
  const [silenceDuration, setSilenceDuration] = useState<number>(5)

  // SRT output configuration
  const [srtEnabled, setSrtEnabled] = useState(true)
  const [srtMode, setSrtMode] = useState<string>('caller')
  const [srtHost, setSrtHost] = useState<string>('localhost')
  const [srtPort, setSrtPort] = useState<number>(9000)
  const [srtLatency, setSrtLatency] = useState<number>(200)
  const [srtPassphrase, setSrtPassphrase] = useState<string>('')
  const [srtCodec, setSrtCodec] = useState<string>('opus')
  const [srtBitrate, setSrtBitrate] = useState<number>(128)
  const [srtContainer, setSrtContainer] = useState<string>('matroska')

  // GPIO configuration
  const [gpioTcpEnabled, setGpioTcpEnabled] = useState(false)
  const [gpioTcpPort, setGpioTcpPort] = useState<number>(7000)
  const [gpioHttpEnabled, setGpioHttpEnabled] = useState(false)
  const [gpioHttpPort, setGpioHttpPort] = useState<number>(8080)

  // Metadata configuration
  const [metadataEnabled, setMetadataEnabled] = useState(true)
  const [metadataWebsocket, setMetadataWebsocket] = useState(true)

  useEffect(() => {
    fetchDevices()
    fetchPresets()

    if (flowId) {
      fetchFlowConfig()
    }
  }, [flowId])

  const fetchDevices = async () => {
    try {
      const response = await apiClient.get<Device[]>('/devices')
      setDevices(response.data)
    } catch (error) {
      console.error('Error fetching devices:', error)
    }
  }

  const fetchPresets = async () => {
    try {
      const response = await apiClient.get<StereoToolPreset[]>('/stereotool/presets')
      setPresets(response.data)
    } catch (error) {
      console.error('Error fetching presets:', error)
    }
  }

  const fetchFlowConfig = async () => {
    // TODO: Fetch existing Flow configuration for editing
    // This would load all the form fields with existing values
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const flowConfig = {
        config: {
          id: flowId || flowName.toLowerCase().replace(/\s+/g, '_'),
          name: flowName,
          enabled,
          inputs: [
            {
              type: inputType,
              device: inputDevice,
              channels: inputChannels,
              sample_rate: inputSampleRate,
              priority: 1
            }
          ],
          processing: {
            stereotool: {
              enabled: stereoToolEnabled,
              preset: selectedPreset ? `/opt/streon/liquidsoap/stereotool/presets/${selectedPreset}.sts` : ''
            },
            silence_detection: {
              threshold_dbfs: silenceThreshold,
              duration_s: silenceDuration
            },
            crossfade: {
              enabled: false,
              duration_s: 2
            }
          },
          outputs: {
            srt: srtEnabled ? [{
              mode: srtMode,
              host: srtHost,
              port: srtPort,
              latency_ms: srtLatency,
              passphrase: srtPassphrase,
              codec: srtCodec,
              bitrate_kbps: srtBitrate,
              container: srtContainer
            }] : [],
            alsa: []
          },
          gpio: {
            tcp_input: {
              enabled: gpioTcpEnabled,
              port: gpioTcpPort
            },
            http_input: {
              enabled: gpioHttpEnabled,
              port: gpioHttpPort
            },
            tcp_output: {
              enabled: false,
              host: 'localhost',
              port: 7001
            },
            embed_in_srt: false
          },
          metadata: {
            enabled: metadataEnabled,
            websocket: metadataWebsocket,
            embed_in_srt: false,
            rest_endpoint: true
          },
          monitoring: {
            metering: true,
            silence_detection: true,
            srt_stats: true,
            prometheus: true
          }
        }
      }

      if (flowId) {
        // Update existing Flow
        await apiClient.put(`/flows/${flowId}`, flowConfig.config)
      } else {
        // Create new Flow
        await apiClient.post('/flows', flowConfig)
      }

      onSave()
    } catch (error) {
      console.error('Error saving Flow:', error)
      alert('Failed to save Flow')
    } finally {
      setLoading(false)
    }
  }

  const availableDevices = devices.filter(d => d.type === inputType && d.is_available)

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6">
        {flowId ? 'Edit Flow' : 'Create New Flow'}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="border-b border-gray-700 pb-6">
          <h3 className="text-lg font-semibold mb-4">Basic Information</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Flow Name</label>
              <input
                type="text"
                value={flowName}
                onChange={(e) => setFlowName(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                placeholder="Main Program Feed"
                required
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="ml-2 text-sm">Enable Flow on creation</label>
            </div>
          </div>
        </div>

        {/* Input Configuration */}
        <div className="border-b border-gray-700 pb-6">
          <h3 className="text-lg font-semibold mb-4">Input Source</h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Input Type</label>
              <select
                value={inputType}
                onChange={(e) => setInputType(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="alsa">ALSA Device</option>
                <option value="usb">USB Audio</option>
                <option value="inferno_rx">Dante (Inferno RX)</option>
                <option value="srt">SRT Input</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Device</label>
              <select
                value={inputDevice}
                onChange={(e) => setInputDevice(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                required
              >
                <option value="">Select device...</option>
                {availableDevices.map((device) => (
                  <option key={device.id} value={device.device_name}>
                    {device.friendly_name || device.device_name} ({device.channels}ch @ {device.sample_rate}Hz)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Channels</label>
              <input
                type="number"
                value={inputChannels}
                onChange={(e) => setInputChannels(parseInt(e.target.value))}
                min="1"
                max="8"
                className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Sample Rate (Hz)</label>
              <select
                value={inputSampleRate}
                onChange={(e) => setInputSampleRate(parseInt(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              >
                <option value={44100}>44100</option>
                <option value={48000}>48000</option>
                <option value={96000}>96000</option>
              </select>
            </div>
          </div>
        </div>

        {/* Processing Configuration */}
        <div className="border-b border-gray-700 pb-6">
          <h3 className="text-lg font-semibold mb-4">Audio Processing</h3>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={stereoToolEnabled}
                onChange={(e) => setStereoToolEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="ml-2 text-sm font-medium">Enable StereoTool Processing</label>
            </div>

            {stereoToolEnabled && (
              <div>
                <label className="block text-sm font-medium mb-2">StereoTool Preset</label>
                <select
                  value={selectedPreset}
                  onChange={(e) => setSelectedPreset(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required={stereoToolEnabled}
                >
                  <option value="">Select preset...</option>
                  {presets.map((preset) => (
                    <option key={preset.id} value={preset.id}>
                      {preset.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Silence Threshold (dBFS)</label>
                <input
                  type="number"
                  value={silenceThreshold}
                  onChange={(e) => setSilenceThreshold(parseInt(e.target.value))}
                  min="-100"
                  max="0"
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Silence Duration (seconds)</label>
                <input
                  type="number"
                  value={silenceDuration}
                  onChange={(e) => setSilenceDuration(parseInt(e.target.value))}
                  min="1"
                  max="60"
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* SRT Output Configuration */}
        <div className="border-b border-gray-700 pb-6">
          <h3 className="text-lg font-semibold mb-4">SRT Transport Output</h3>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={srtEnabled}
                onChange={(e) => setSrtEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="ml-2 text-sm font-medium">Enable SRT Output</label>
            </div>

            {srtEnabled && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Mode</label>
                    <select
                      value={srtMode}
                      onChange={(e) => setSrtMode(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="caller">Caller (connect to receiver)</option>
                      <option value="listener">Listener (wait for connections)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Host</label>
                    <input
                      type="text"
                      value={srtHost}
                      onChange={(e) => setSrtHost(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                      placeholder="srt.example.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Port</label>
                    <input
                      type="number"
                      value={srtPort}
                      onChange={(e) => setSrtPort(parseInt(e.target.value))}
                      min="1"
                      max="65535"
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Latency (ms)</label>
                    <input
                      type="number"
                      value={srtLatency}
                      onChange={(e) => setSrtLatency(parseInt(e.target.value))}
                      min="20"
                      max="8000"
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Codec</label>
                    <select
                      value={srtCodec}
                      onChange={(e) => setSrtCodec(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="opus">Opus</option>
                      <option value="aac">AAC</option>
                      <option value="pcm">PCM (uncompressed)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Bitrate (kbps)</label>
                    <input
                      type="number"
                      value={srtBitrate}
                      onChange={(e) => setSrtBitrate(parseInt(e.target.value))}
                      min="32"
                      max="512"
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-2">Passphrase (optional)</label>
                    <input
                      type="password"
                      value={srtPassphrase}
                      onChange={(e) => setSrtPassphrase(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                      placeholder="Leave empty for no encryption"
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* GPIO Configuration */}
        <div className="border-b border-gray-700 pb-6">
          <h3 className="text-lg font-semibold mb-4">GPIO Automation</h3>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={gpioTcpEnabled}
                onChange={(e) => setGpioTcpEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="ml-2 text-sm">Enable TCP GPIO Input</label>
            </div>

            {gpioTcpEnabled && (
              <div>
                <label className="block text-sm font-medium mb-2">TCP Port</label>
                <input
                  type="number"
                  value={gpioTcpPort}
                  onChange={(e) => setGpioTcpPort(parseInt(e.target.value))}
                  min="1024"
                  max="65535"
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={gpioHttpEnabled}
                onChange={(e) => setGpioHttpEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="ml-2 text-sm">Enable HTTP GPIO Input</label>
            </div>

            {gpioHttpEnabled && (
              <div>
                <label className="block text-sm font-medium mb-2">HTTP Port</label>
                <input
                  type="number"
                  value={gpioHttpPort}
                  onChange={(e) => setGpioHttpPort(parseInt(e.target.value))}
                  min="1024"
                  max="65535"
                  className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}
          </div>
        </div>

        {/* Metadata Configuration */}
        <div className="pb-6">
          <h3 className="text-lg font-semibold mb-4">Metadata</h3>

          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={metadataEnabled}
                onChange={(e) => setMetadataEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="ml-2 text-sm">Enable Metadata Extraction</label>
            </div>

            {metadataEnabled && (
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={metadataWebsocket}
                  onChange={(e) => setMetadataWebsocket(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <label className="ml-2 text-sm">Enable WebSocket Streaming</label>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving...' : flowId ? 'Update Flow' : 'Create Flow'}
          </button>

          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
