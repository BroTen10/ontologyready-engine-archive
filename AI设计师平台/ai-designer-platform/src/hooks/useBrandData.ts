import { useState, useEffect } from 'react'
import type { BrandProfilesData, Project } from '@/types'

export function useBrandData() {
  const [data, setData] = useState<BrandProfilesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch('/data/brand_profiles.json')
        if (!response.ok) {
          throw new Error('Failed to load brand profiles')
        }
        const jsonData = await response.json()
        setData(jsonData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Create new project
  const createProject = (project: Omit<Project, 'id'>) => {
    if (!data) return null
    
    const newProject: Project = {
      ...project,
      id: `project-${Date.now()}`
    }
    
    const updatedData = {
      ...data,
      projects: [...data.projects, newProject]
    }
    
    setData(updatedData)
    return newProject
  }

  // Delete project
  const deleteProject = (projectId: string) => {
    if (!data) return false
    
    const updatedProjects = data.projects.filter(project => project.id !== projectId)
    
    const updatedData = {
      ...data,
      projects: updatedProjects
    }
    
    setData(updatedData)
    return true
  }

  // Update project
  const updateProject = (projectId: string, updates: Partial<Project>) => {
    if (!data) return null
    
    const updatedProjects = data.projects.map(project => 
      project.id === projectId 
        ? { ...project, ...updates, updated_at: new Date().toISOString() } 
        : project
    )
    
    const updatedData = {
      ...data,
      projects: updatedProjects
    }
    
    setData(updatedData)
    return updatedProjects.find(project => project.id === projectId) || null
  }

  return { 
    data, 
    loading, 
    error,
    createProject,
    deleteProject,
    updateProject
  }
}
