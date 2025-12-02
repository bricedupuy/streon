import { useState, useEffect, useRef } from 'react'
import { apiClient } from '@/api/client'

interface FlowMonitorProps {
  flowId: string
}

interface AudioLevels {
  peak_l: number
  peak_r: number
  rms_l: number
  rms_r: number
}

interface SRTStats {
  rtt_ms: number
  packet_loss: number
  bitrate_kbps: number
}

interface MetadataInfo {
  artist: string | null
  title: string | null
  timestamp: string
}

export default function FlowMonitor({ flowId }: FlowMonitorProps) {
  const [audioLevels, setAudioLevels] = useState<AudioLevels>({
    peak_l: -60,
    peak_r: -60,
    rms_l: -60,
    rms_r: -60
  })
  const [srtStats, setSrtStats] = useState<SRTStats | null>(null)
  const [metadata, setMetadata] = useState<MetadataInfo | null>(null)
  const [silenceDuration, setSilenceDuration] = useState<number>(0)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Connect to metadata WebSocket
    const wsUrl = `ws://localhost:8000/api/v1/metadata/stream`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log(`Connected to metadata WebSocket for Flow ${flowId}`)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.flow_id === flowId) {
          setMetadata({
            artist: data.artist,
            title: data.title,
            timestamp: data.timestamp
          })
        }
      } catch (error) {
        console.error('Error parsing metadata:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
    }

    wsRef.current = ws

    // Simulated audio level updates (in production, this would come from Liquidsoap telnet)
    const audioInterval = setInterval(() => {
      // Simulate realistic audio levels with some variance
      const randomPeak = () => -20 + Math.random() * 15
      const randomRms = () => -30 + Math.random() * 15

      setAudioLevels({
        peak_l: randomPeak(),
        peak_r: randomPeak(),
        rms_l: randomRms(),
        rms_r: randomRms()
      })
    }, 100) // Update 10 times per second

    // Fetch SRT stats periodically
    const srtInterval = setInterval(async () => {
      try {
        // In production, this would be a real endpoint
        // const response = await apiClient.get(`/flows/${flowId}/srt-stats`)
        // setSrtStats(response.data)

        // Simulated SRT stats
        setSrtStats({
          rtt_ms: 15 + Math.random() * 10,
          packet_loss: Math.random() * 0.001,
          bitrate_kbps: 128 + Math.random() * 5
        })
      } catch (error) {
        console.error('Error fetching SRT stats:', error)
      }
    }, 2000)

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      clearInterval(audioInterval)
      clearInterval(srtInterval)
    }
  }, [flowId])

  return (
    <div className="space-y-6">
      {/* Audio Meters */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Audio Levels</h3>

        <div className="space-y-4">
          {/* Left Channel */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Left Channel</span>
              <span className="font-mono">{audioLevels.peak_l.toFixed(1)} dBFS</span>
            </div>
            <AudioMeter level={audioLevels.peak_l} channel="L" />
          </div>

          {/* Right Channel */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Right Channel</span>
              <span className="font-mono">{audioLevels.peak_r.toFixed(1)} dBFS</span>
            </div>
            <AudioMeter level={audioLevels.peak_r} channel="R" />
          </div>
        </div>

        {/* Silence Indicator */}
        {silenceDuration > 5 && (
          <div className="mt-4 p-3 bg-red-900/30 border border-red-500 rounded">
            <p className="text-red-400 font-medium">
              ⚠️ Silence detected: {silenceDuration.toFixed(0)}s
            </p>
          </div>
        )}
      </div>

      {/* SRT Transport Stats */}
      {srtStats && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">SRT Transport</h3>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-1">Round-Trip Time</p>
              <p className="text-2xl font-bold">{srtStats.rtt_ms.toFixed(1)} ms</p>
              <div className={`mt-2 h-1 rounded ${srtStats.rtt_ms < 100 ? 'bg-green-500' : srtStats.rtt_ms < 300 ? 'bg-yellow-500' : 'bg-red-500'}`} />
            </div>

            <div>
              <p className="text-sm text-gray-400 mb-1">Packet Loss</p>
              <p className="text-2xl font-bold">{(srtStats.packet_loss * 100).toFixed(3)}%</p>
              <div className={`mt-2 h-1 rounded ${srtStats.packet_loss < 0.001 ? 'bg-green-500' : srtStats.packet_loss < 0.01 ? 'bg-yellow-500' : 'bg-red-500'}`} />
            </div>

            <div>
              <p className="text-sm text-gray-400 mb-1">Bitrate</p>
              <p className="text-2xl font-bold">{srtStats.bitrate_kbps.toFixed(0)} kbps</p>
              <div className="mt-2 h-1 rounded bg-blue-500" />
            </div>
          </div>
        </div>
      )}

      {/* Current Metadata */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Now Playing</h3>

        {metadata ? (
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gray-700 rounded flex items-center justify-center">
                <span className="text-2xl">🎵</span>
              </div>
              <div>
                <p className="font-semibold text-lg">{metadata.title || 'Unknown Title'}</p>
                <p className="text-gray-400">{metadata.artist || 'Unknown Artist'}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Last updated: {new Date(metadata.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ) : (
          <p className="text-gray-400">No metadata available</p>
        )}
      </div>
    </div>
  )
}

function AudioMeter({ level, channel }: { level: number; channel: string }) {
  // Convert dBFS to percentage (0 dBFS = 100%, -60 dBFS = 0%)
  const percentage = Math.max(0, Math.min(100, ((level + 60) / 60) * 100))

  // Determine color based on level
  const getColor = () => {
    if (level > -3) return 'bg-red-500' // Clipping range
    if (level > -6) return 'bg-red-400'
    if (level > -12) return 'bg-yellow-500'
    if (level > -20) return 'bg-yellow-400'
    return 'bg-green-500'
  }

  return (
    <div className="relative h-8 bg-gray-700 rounded overflow-hidden">
      {/* Level bar */}
      <div
        className={`absolute left-0 top-0 h-full transition-all duration-100 ${getColor()}`}
        style={{ width: `${percentage}%` }}
      />

      {/* Scale markers */}
      <div className="absolute inset-0 flex items-center">
        {[-60, -40, -20, -12, -6, -3, 0].map((db) => {
          const pos = ((db + 60) / 60) * 100
          return (
            <div
              key={db}
              className="absolute h-full w-px bg-gray-900"
              style={{ left: `${pos}%` }}
            >
              {db === 0 || db === -12 || db === -20 ? (
                <span className="absolute top-0 -translate-x-1/2 text-xs text-gray-400 -mt-5">
                  {db}
                </span>
              ) : null}
            </div>
          )
        })}
      </div>

      {/* Channel label */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-gray-300">
        {channel}
      </div>
    </div>
  )
}
