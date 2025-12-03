import { apiClient } from './client'

export interface StereoToolLicense {
  id: string
  name: string
  license_key: string  // Partial key for display
  added_at: string
  is_valid: boolean
}

export interface StereoToolPreset {
  id: string
  name: string
  filename: string
  uploaded_at: string
  file_size: number
  description?: string
  is_default: boolean
}

export const stereoToolApi = {
  // Licenses
  addLicense: async (licenseKey: string, name: string): Promise<StereoToolLicense> => {
    const formData = new FormData()
    formData.append('license_key', licenseKey)
    formData.append('name', name)
    const response = await apiClient.post<StereoToolLicense>('/stereotool/licenses', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  listLicenses: async (): Promise<StereoToolLicense[]> => {
    const response = await apiClient.get<StereoToolLicense[]>('/stereotool/licenses')
    return response.data
  },

  deleteLicense: async (licenseId: string): Promise<void> => {
    await apiClient.delete(`/stereotool/licenses/${licenseId}`)
  },

  // Presets
  uploadPreset: async (file: File, name: string, description?: string): Promise<StereoToolPreset> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    if (description) {
      formData.append('description', description)
    }
    const response = await apiClient.post<StereoToolPreset>('/stereotool/presets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  listPresets: async (): Promise<StereoToolPreset[]> => {
    const response = await apiClient.get<StereoToolPreset[]>('/stereotool/presets')
    return response.data
  },

  getPreset: async (presetId: string): Promise<StereoToolPreset> => {
    const response = await apiClient.get<StereoToolPreset>(`/stereotool/presets/${presetId}`)
    return response.data
  },

  activatePreset: async (presetId: string): Promise<void> => {
    await apiClient.put(`/stereotool/presets/${presetId}/activate`)
  },

  deletePreset: async (presetId: string): Promise<void> => {
    await apiClient.delete(`/stereotool/presets/${presetId}`)
  },

  downloadPreset: async (presetId: string): Promise<Blob> => {
    const response = await apiClient.get(`/stereotool/presets/${presetId}/download`, {
      responseType: 'blob',
    })
    return response.data
  },
}
