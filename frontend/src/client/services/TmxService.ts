// This file is autogenerated, do not edit directly.

import {getApiBase, api} from '../defaults'

import {TmxFile} from '../schemas/TmxFile'
import {Body_create_tmx_tmx__post} from '../schemas/Body_create_tmx_tmx__post'
import {TmxFileWithRecordsCount} from '../schemas/TmxFileWithRecordsCount'
import {StatusMessage} from '../schemas/StatusMessage'
import {TmxFileRecord} from '../schemas/TmxFileRecord'

export const getTmxs = async (): Promise<TmxFile[]> => {
  return await api.get<TmxFile[]>(`/tmx/`)
}
export const createTmx = async (data: Body_create_tmx_tmx__post): Promise<TmxFile> => {
  const formData = new FormData()
  formData.append('file', data.file)
  return await api.post<TmxFile>(`/tmx/`, formData)
}
export const getTmx = async (tmx_id: number): Promise<TmxFileWithRecordsCount> => {
  return await api.get<TmxFileWithRecordsCount>(`/tmx/${tmx_id}`)
}
export const deleteTmx = async (tmx_id: number): Promise<StatusMessage> => {
  return await api.delete<StatusMessage>(`/tmx/${tmx_id}`)
}
export const getTmxRecords = async (tmx_id: number, page?: number | null): Promise<TmxFileRecord[]> => {
  return await api.get<TmxFileRecord[]>(`/tmx/${tmx_id}/records`, {query: {page}})
}
