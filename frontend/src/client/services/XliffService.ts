// This file is autogenerated, do not edit directly.

import {defaults, mande} from 'mande'

import {getApiBase} from '../defaults'

import {XliffFile} from '../schemas/XliffFile'
import {Body_create_xliff_xliff__post} from '../schemas/Body_create_xliff_xliff__post'
import {XliffFileWithRecords} from '../schemas/XliffFileWithRecords'
import {StatusMessage} from '../schemas/StatusMessage'

export const getXliffs = async (): Promise<XliffFile[]> => {
  const api = mande(getApiBase() + `/xliff/`)
  return await api.get<XliffFile[]>('')
}
export const createXliff = async (data: Body_create_xliff_xliff__post): Promise<XliffFile> => {
  const formData = new FormData()
  formData.append('file', data.file)
  const defaultHeaders = defaults.headers
  try {
    const api = mande(getApiBase() + `/xliff/`)
    defaults.headers = {}
    return await api.post<XliffFile>('', formData)
  } catch (error: any) {
    throw error
  } finally {
    defaults.headers = defaultHeaders
  }
}
export const getXliff = async (doc_id: number): Promise<XliffFileWithRecords> => {
  const api = mande(getApiBase() + `/xliff/${doc_id}`)
  return await api.get<XliffFileWithRecords>('')
}
export const deleteXliff = async (doc_id: number): Promise<StatusMessage> => {
  const api = mande(getApiBase() + `/xliff/${doc_id}`)
  return await api.delete<StatusMessage>('')
}
export const getDownloadXliffLink = (doc_id: number): string => {
  return getApiBase() + `/xliff/${doc_id}/download`
}