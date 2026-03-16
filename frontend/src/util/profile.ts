import { BASE_URL, maybeHandleExpire } from './api'
import type { UserProfile } from '../types/profile'

export const getProfile = async (id?: string) => {
  const endpoint = id ? `${BASE_URL}/user/${id}` : `${BASE_URL}/user/`
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include'
  })

  maybeHandleExpire(response)

  if (!response.ok) {
    throw new Error(`Failed to fetch profile: ${response.status}`)
  }

  return await response.json() as UserProfile
}

export const uploadProfilePicture = async (file: File) => {
  const formData = new FormData()
  formData.append('profile_picture', file)

  const response = await fetch(`${BASE_URL}/user/profile-picture`, {
    method: 'POST',
    body: formData,
    credentials: 'include'
  })

  maybeHandleExpire(response)

  if (!response.ok) {
    let errorMessage = `Failed to upload profile picture: ${response.status}`
    try {
      const error = await response.json()
      if (error?.msg) {
        errorMessage = error.msg
      }
    } catch {
      // Keep fallback message.
    }
    throw new Error(errorMessage)
  }

  return await response.json() as UserProfile
}

export const deleteProfilePicture = async () => {
  const response = await fetch(`${BASE_URL}/user/profile-picture`, {
    method: 'DELETE',
    credentials: 'include'
  })

  maybeHandleExpire(response)

  if (!response.ok) {
    let errorMessage = `Failed to delete profile picture: ${response.status}`
    try {
      const error = await response.json()
      if (error?.msg) {
        errorMessage = error.msg
      }
    } catch {
      // Keep fallback message.
    }
    throw new Error(errorMessage)
  }

  return await response.json() as UserProfile
}

export const getProfilePictureSrc = (profilePictureUrl: string | null | undefined, version = 0) => {
  if (!profilePictureUrl) {
    return null
  }

  return `${BASE_URL}${profilePictureUrl}?v=${version}`
}