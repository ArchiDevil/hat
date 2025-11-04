import {describe, it, expect, beforeEach} from 'vitest'
import {createPinia, setActivePinia} from 'pinia'
import {useUserStore} from '../stores/user'
import {isAdmin} from './auth'

describe('auth utilities', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should return false when user is not logged in', () => {
    const userStore = useUserStore()
    userStore.currentUser = undefined

    expect(isAdmin()).toBe(false)
  })

  it('should return false when user role is user', () => {
    const userStore = useUserStore()
    userStore.currentUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      disabled: false
    }

    expect(isAdmin()).toBe(false)
  })

  it('should return true when user role is admin', () => {
    const userStore = useUserStore()
    userStore.currentUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin',
      disabled: false
    }

    expect(isAdmin()).toBe(true)
  })
})
