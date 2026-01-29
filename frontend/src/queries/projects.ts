import {defineQuery, useQuery} from '@pinia/colada'
import {listProjects} from '../client/services/ProjectsService'

export const PROJECT_KEYS = {
  root: ['projects'] as const,
  byId: (projectId: number) => [...PROJECT_KEYS.root, projectId] as const,
}

export const useProjects = defineQuery(() => {
  const data = useQuery({
    key: () => PROJECT_KEYS.root,
    query: async () => {
      return await listProjects()
    },
    placeholderData: <T>(prevData: T) => prevData,
  })
  return data
})
