import {useUserStore} from '../stores/user'

/**
 * Check if the current user is an administrator
 * @returns boolean - true if user is admin, false otherwise
 */
export const isAdmin = (): boolean => {
  const userStore = useUserStore()
  return userStore.currentUser?.role === 'admin'
}
