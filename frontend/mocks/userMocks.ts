import {http, HttpResponse} from 'msw'
import {AwaitedReturnType} from './utils'
import {getCurrentUser} from '../src/client/services/UserService'
import {UserWithPermissions} from '../src/client/schemas/UserWithPermissions'

export const defaultUser: UserWithPermissions = {
  id: 12,
  email: 'test@example.com',
  role: 'admin',
  username: 'test',
  disabled: false,
  permissions: [
    'glossary:read',
    'glossary:upload',
    'glossary:download',
    'glossary:create',
    'glossary:update',
    'glossary:delete',
    'glossary_record:create',
    'tm:read',
    'tm:create',
    'tm:delete',
    'tm:upload',
    'tm:download',
    'record:read',
    'record:edit',
    'document:read',
    'document:create',
    'document:delete',
    'document:update',
    'document:download',
    'document:process',
    'project:read',
    'project:create',
    'project:update',
    'project:delete',
    'project:manage_resources',
    'comment:create',
    'comment:manage',
    'user:manage',
  ],
}

export const userMocks = [
  http.get('http://localhost:8000/user/', () =>
    HttpResponse.json<AwaitedReturnType<typeof getCurrentUser>>(defaultUser)
  ),
]
