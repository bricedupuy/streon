import { useState, useEffect } from 'react'
import { stereoToolApi, StereoToolPreset, StereoToolLicense } from '@/api/stereotool'

export default function StereoToolPage() {
  const [presets, setPresets] = useState<StereoToolPreset[]>([])
  const [licenses, setLicenses] = useState<StereoToolLicense[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [presetsData, licensesData] = await Promise.all([
        stereoToolApi.listPresets(),
        stereoToolApi.listLicenses(),
      ])
      setPresets(presetsData)
      setLicenses(licensesData)
    } catch (error) {
      console.error('Error fetching StereoTool data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePresetUpload = async (file: File, name: string, description?: string) => {
    setUploading(true)
    try {
      await stereoToolApi.uploadPreset(file, name, description)
      await fetchData()
      alert('Preset uploaded successfully!')
    } catch (error) {
      console.error('Error uploading preset:', error)
      alert('Failed to upload preset')
    } finally {
      setUploading(false)
    }
  }

  const handleAddLicense = async (licenseKey: string, name: string) => {
    setUploading(true)
    try {
      await stereoToolApi.addLicense(licenseKey, name)
      await fetchData()
      alert('License added successfully!')
    } catch (error) {
      console.error('Error adding license:', error)
      alert('Failed to add license')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteLicense = async (licenseId: string) => {
    if (!confirm('Are you sure you want to delete this license?')) return

    try {
      await stereoToolApi.deleteLicense(licenseId)
      await fetchData()
    } catch (error) {
      console.error('Error deleting license:', error)
      alert('Failed to delete license')
    }
  }

  const handleActivatePreset = async (presetId: string) => {
    try {
      await stereoToolApi.activatePreset(presetId)
      await fetchData()
      alert('Preset activated as default!')
    } catch (error) {
      console.error('Error activating preset:', error)
      alert('Failed to activate preset')
    }
  }

  const handleDeletePreset = async (presetId: string) => {
    if (!confirm('Are you sure you want to delete this preset?')) return

    try {
      await stereoToolApi.deletePreset(presetId)
      await fetchData()
    } catch (error) {
      console.error('Error deleting preset:', error)
      alert('Failed to delete preset')
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">StereoTool Management</h1>

      {/* Licenses Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Licenses</h2>
        <div className="bg-gray-800 rounded-lg p-6">
          <LicenseInput onAdd={handleAddLicense} uploading={uploading} />

          {licenses.length > 0 ? (
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-3">Added Licenses</h3>
              <div className="space-y-2">
                {licenses.map((license) => (
                  <div key={license.id} className="bg-gray-700 rounded p-4 flex justify-between items-center">
                    <div className="flex-1">
                      <p className="font-medium">{license.name}</p>
                      <p className="text-sm text-gray-400 font-mono">{license.license_key}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Added: {new Date(license.added_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className={`px-3 py-1 rounded ${license.is_valid ? 'bg-green-600' : 'bg-red-600'}`}>
                        {license.is_valid ? 'Valid' : 'Invalid'}
                      </div>
                      <button
                        onClick={() => handleDeleteLicense(license.id)}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-400 mt-4">No licenses added yet</p>
          )}
        </div>
      </div>

      {/* Presets Section */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Presets</h2>
        <div className="bg-gray-800 rounded-lg p-6">
          <PresetUpload onUpload={handlePresetUpload} uploading={uploading} />

          {presets.length > 0 ? (
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-3">Uploaded Presets</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {presets.map((preset) => (
                  <div key={preset.id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-semibold text-lg">{preset.name}</h4>
                        {preset.is_default && (
                          <span className="inline-block px-2 py-1 bg-blue-600 text-xs rounded mt-1">
                            Default
                          </span>
                        )}
                      </div>
                    </div>

                    {preset.description && (
                      <p className="text-sm text-gray-300 mb-3">{preset.description}</p>
                    )}

                    <p className="text-xs text-gray-400 mb-3">
                      {preset.filename} • {(preset.file_size / 1024).toFixed(1)} KB
                    </p>

                    <div className="flex space-x-2">
                      {!preset.is_default && (
                        <button
                          onClick={() => handleActivatePreset(preset.id)}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                        >
                          Set as Default
                        </button>
                      )}
                      <button
                        onClick={() => handleDeletePreset(preset.id)}
                        className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-400 mt-4">No presets uploaded yet</p>
          )}
        </div>
      </div>
    </div>
  )
}

function LicenseInput({ onAdd, uploading }: { onAdd: (licenseKey: string, name: string) => void; uploading: boolean }) {
  const [licenseKey, setLicenseKey] = useState('')
  const [name, setName] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!licenseKey.trim() || !name.trim()) {
      alert('Please provide both license key and name')
      return
    }
    onAdd(licenseKey, name)
    setLicenseKey('')
    setName('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2">License Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Main Studio License"
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
          disabled={uploading}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">License Key</label>
        <textarea
          value={licenseKey}
          onChange={(e) => setLicenseKey(e.target.value)}
          placeholder="Paste your StereoTool license key here..."
          rows={3}
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none font-mono text-sm"
          disabled={uploading}
        />
      </div>

      <button
        type="submit"
        disabled={uploading || !licenseKey.trim() || !name.trim()}
        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? 'Adding...' : 'Add License'}
      </button>
    </form>
  )
}

// Keep the old LicenseUpload component for reference but rename it
function OldLicenseUpload_Unused({ onUpload, uploading }: { onUpload: (file: File) => void; uploading: boolean }) {
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0])
    }
  }

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 text-center ${
        dragActive ? 'border-blue-500 bg-blue-900/20' : 'border-gray-600'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="license-upload"
        className="hidden"
        onChange={handleChange}
        accept=".key"
        disabled={uploading}
      />
      <label htmlFor="license-upload" className="cursor-pointer">
        <p className="text-lg mb-2">
          {uploading ? 'Uploading...' : 'Drop license file here or click to browse'}
        </p>
        <p className="text-sm text-gray-400">Accepts .key files</p>
      </label>
    </div>
  )
}

function PresetUpload({ onUpload, uploading }: { onUpload: (file: File, name: string, desc?: string) => void; uploading: boolean }) {
  const [dragActive, setDragActive] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0])
      setShowForm(true)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setShowForm(true)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedFile && name) {
      onUpload(selectedFile, name, description || undefined)
      setSelectedFile(null)
      setName('')
      setDescription('')
      setShowForm(false)
    }
  }

  if (showForm && selectedFile) {
    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">File: {selectedFile.name}</label>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Preset Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            placeholder="e.g., FM Broadcast"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Description (optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-4 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            placeholder="e.g., Heavy compression for FM broadcast"
            rows={3}
          />
        </div>
        <div className="flex space-x-2">
          <button
            type="submit"
            disabled={uploading || !name}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload Preset'}
          </button>
          <button
            type="button"
            onClick={() => {
              setShowForm(false)
              setSelectedFile(null)
              setName('')
              setDescription('')
            }}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    )
  }

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 text-center ${
        dragActive ? 'border-blue-500 bg-blue-900/20' : 'border-gray-600'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="preset-upload"
        className="hidden"
        onChange={handleChange}
        accept=".sts"
        disabled={uploading}
      />
      <label htmlFor="preset-upload" className="cursor-pointer">
        <p className="text-lg mb-2">
          {uploading ? 'Uploading...' : 'Drop preset file here or click to browse'}
        </p>
        <p className="text-sm text-gray-400">Accepts .sts files</p>
      </label>
    </div>
  )
}
