import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// API URL - change this if your backend is hosted elsewhere
const API_URL = 'http://localhost:8000/api'

export const api = {
    getAlerts: async () => {
        try {
            const response = await fetch(`${API_URL}/alerts`)
            if (!response.ok) throw new Error('Failed to fetch alerts')
            return await response.json()
        } catch (error) {
            console.error('Error fetching alerts:', error)
            return []
        }
    },

    getStats: async () => {
        try {
            const response = await fetch(`${API_URL}/stats`)
            if (!response.ok) throw new Error('Failed to fetch stats')
            return await response.json()
        } catch (error) {
            console.error('Error fetching stats:', error)
            return []
        }
    },

    getStatus: async () => {
        try {
            const response = await fetch(`${API_URL}/status`)
            if (!response.ok) throw new Error('Failed to fetch status')
            return await response.json()
        } catch (error) {
            console.error('Error fetching status:', error)
            return null
        }
    },

    getHistory: async (limit = 20) => {
        try {
            const response = await fetch(`${API_URL}/stats/history?limit=${limit}`)
            if (!response.ok) throw new Error('Failed to fetch history')
            return await response.json()
        } catch (error) {
            console.error('Error fetching history:', error)
            return []
        }
    },

    getTopSources: async () => {
        try {
            const response = await fetch(`${API_URL}/analytics/top-sources`)
            if (!response.ok) throw new Error('Failed to fetch top sources')
            return await response.json()
        } catch (error) {
            console.error('Error fetching top sources:', error)
            return []
        }
    },

    getGeoDistribution: async () => {
        try {
            const response = await fetch(`${API_URL}/analytics/geo`)
            if (!response.ok) throw new Error('Failed to fetch geo distribution')
            return await response.json()
        } catch (error) {
            console.error('Error fetching geo distribution:', error)
            return []
        }
    },

    getLogs: async () => {
        try {
            const response = await fetch(`${API_URL}/logs`)
            if (!response.ok) throw new Error('Failed to fetch logs')
            return await response.json()
        } catch (error) {
            console.error('Error fetching logs:', error)
            return []
        }
    },

    getDevices: async () => {
        try {
            const response = await fetch(`${API_URL}/devices`)
            if (!response.ok) throw new Error('Failed to fetch devices')
            return await response.json()
        } catch (error) {
            console.error('Error fetching devices:', error)
            return []
        }
    }
}
