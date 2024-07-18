// This file is autogenerated, do not edit directly.

import {mande} from 'mande'

export const getApiBase = () => {
  if (import.meta.env.DEV) {
    return 'http://localhost:8000'
  } else {
    return '/api'
  }
}

export const api = mande(getApiBase())
