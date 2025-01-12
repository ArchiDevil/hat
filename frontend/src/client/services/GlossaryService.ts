// This file is autogenerated, do not edit directly.

import {getApiBase, api} from '../defaults'

import {GlossaryResponse} from '../schemas/GlossaryResponse'
import {GlossarySchema} from '../schemas/GlossarySchema'
import {StatusMessage} from '../schemas/StatusMessage'
import {GlossaryRecordSchema} from '../schemas/GlossaryRecordSchema'
import {GlossaryRecordCreate} from '../schemas/GlossaryRecordCreate'
import {GlossaryRecordUpdate} from '../schemas/GlossaryRecordUpdate'
import {GlossaryLoadFileResponse} from '../schemas/GlossaryLoadFileResponse'
import {Body_create_glossary_from_file_glossary_load_file_post} from '../schemas/Body_create_glossary_from_file_glossary_load_file_post'

export const listGlossary = async (): Promise<GlossaryResponse[]> => {
  return await api.get<GlossaryResponse[]>(`/glossary/`)
}
export const createGlossary = async (content: GlossarySchema): Promise<GlossaryResponse> => {
  return await api.post<GlossaryResponse>(`/glossary/`, content)
}
export const retrieveGlossary = async (glossary_id: number): Promise<GlossaryResponse> => {
  return await api.get<GlossaryResponse>(`/glossary/${glossary_id}`)
}
export const updateGlossary = async (glossary_id: number, content: GlossarySchema): Promise<GlossaryResponse> => {
  return await api.put<GlossaryResponse>(`/glossary/${glossary_id}`, content)
}
export const deleteGlossary = async (glossary_id: number): Promise<StatusMessage> => {
  return await api.delete<StatusMessage>(`/glossary/${glossary_id}`)
}
export const listRecords = async (glossary_id: number | null): Promise<GlossaryRecordSchema[]> => {
  return await api.get<GlossaryRecordSchema[]>(`/glossary/${glossary_id}/records`)
}
export const createGlossaryRecord = async (glossary_id: number, content: GlossaryRecordCreate): Promise<GlossaryRecordSchema> => {
  return await api.post<GlossaryRecordSchema>(`/glossary/${glossary_id}/records`, content)
}
export const updateGlossaryRecord = async (record_id: number, content: GlossaryRecordUpdate): Promise<GlossaryRecordSchema> => {
  return await api.put<GlossaryRecordSchema>(`/glossary/records/${record_id}`, content)
}
export const deleteGlossaryRecord = async (record_id: number): Promise<StatusMessage> => {
  return await api.delete<StatusMessage>(`/glossary/records/${record_id}`)
}
export const createGlossaryFromFile = async (glossary_name: string, data: Body_create_glossary_from_file_glossary_load_file_post): Promise<GlossaryLoadFileResponse> => {
  const formData = new FormData()
  formData.append('file', data.file)
  return await api.post<GlossaryLoadFileResponse>(`/glossary/load_file`, formData, {query: {glossary_name}})
}
