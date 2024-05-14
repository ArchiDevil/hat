// This file is autogenerated, do not edit directly.

import {mande} from 'mande'

import {getApiBase} from '../defaults'

import {XliffFile} from '../schemas/XliffFile'
import {Body_create_xliff_xliff__post} from '../schemas/Body_create_xliff_xliff__post'
import {StatusMessage} from '../schemas/StatusMessage'
import {XliffFileRecord} from '../schemas/XliffFileRecord'
import {XliffProcessingSettings} from '../schemas/XliffProcessingSettings'

export const getXliffs = async (): Promise<XliffFile[]> => {
  const api = mande(getApiBase() + `/xliff/`)
  return await api.get<XliffFile[]>('')
}
export const createXliff = async (data: Body_create_xliff_xliff__post): Promise<XliffFile> => {
  const formData = new FormData()
  formData.append('file', data.file)
  const api = mande(getApiBase() + `/xliff/`)
  return await api.post<XliffFile>('', formData)
}
export const getXliff = async (doc_id: number): Promise<XliffFile> => {
  const api = mande(getApiBase() + `/xliff/${doc_id}`)
  return await api.get<XliffFile>('')
}
export const deleteXliff = async (doc_id: number): Promise<StatusMessage> => {
  const api = mande(getApiBase() + `/xliff/${doc_id}`)
  return await api.delete<StatusMessage>('')
}
export const getXliffRecords = async (doc_id: number): Promise<XliffFileRecord[]> => {
  const api = mande(getApiBase() + `/xliff/${doc_id}/records`)
  return await api.get<XliffFileRecord[]>('')
}
export const processXliff = async (doc_id: number, content: XliffProcessingSettings): Promise<StatusMessage> => {
  const api = mande(getApiBase() + `/xliff/${doc_id}/process`)
  return await api.post<StatusMessage>(content)
}
export const getDownloadXliffLink = (doc_id: number): string => {
  return getApiBase() + `/xliff/${doc_id}/download`
}
