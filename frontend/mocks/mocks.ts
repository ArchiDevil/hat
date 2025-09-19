import {http, passthrough} from 'msw'
import {glossaryMocks} from './glossaryMocks'
import {documentMocks} from './documentMocks'
import {tmMocks} from './tmMocks'
import {userMocks} from './userMocks'

export const mocks = [
  http.get('/src/*', () => passthrough()), // to avoid warnings in dev server
  ...userMocks,
  ...glossaryMocks,
  ...documentMocks,
  ...tmMocks,
]
