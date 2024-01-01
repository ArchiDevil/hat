import {mande} from 'mande'

export function apiAccessor(api: string) {
  if (import.meta.env.DEV) {
    return mande(`http://localhost:5000/api${api}`)
  } else {
    return mande(`/api${api}`)
  }
}
