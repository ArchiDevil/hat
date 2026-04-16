import {P} from '../client/schemas/P'
import {useUserStore} from '../stores/user'

/**
 * Check if the current user is an administrator
 * @returns boolean - true if user is admin, false otherwise
 */
export const isAdmin = (): boolean => {
  const userStore = useUserStore()
  return userStore.currentUser?.role === 'admin'
}

/**
 * Check if the current user has a specific permission
 * @returns boolean - true if permission is set for the user, false otherwise
 */
export const hasPermission = (permission: P): boolean => {
  const userStore = useUserStore()
  return userStore.currentUser?.permissions.includes(permission) ?? false
}
