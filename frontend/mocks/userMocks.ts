import {http, HttpResponse} from 'msw'
import {AwaitedReturnType} from './utils'
import {getCurrentUser} from '../src/client/services/UserService'
import {User} from '../src/client/schemas/User'

export const defaultUser: User = {
  id: 12,
  email: 'test@example.com',
  role: 'user',
  username: 'test',
  disabled: false,
}

export const userMocks = [
  http.get('http://localhost:8000/user/', () =>
    HttpResponse.json<AwaitedReturnType<typeof getCurrentUser>>(defaultUser)
  ),
]
