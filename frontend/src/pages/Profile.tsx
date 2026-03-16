import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import './Profile.css'
import Button from '../components/Button'
import ProfileDetails from '../components/ProfileDetails'
import StatusMessage from '../components/StatusMessage'
import { getCurrentUserId, isTeacher } from '../util/login'
import { deleteProfilePicture, getProfile, getProfilePictureSrc, uploadProfilePicture } from '../util/profile'
import type { UserProfile } from '../types/profile'

export default function Profile() {
  const navigate = useNavigate()
  const { id } = useParams()
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [uploadingPicture, setUploadingPicture] = useState(false)
  const [pictureVersion, setPictureVersion] = useState(0)

  const currentUserId = getCurrentUserId()
  const isOwnProfile = user !== null && currentUserId === user.id
  const profilePictureSrc = getProfilePictureSrc(user?.profile_picture_url, pictureVersion)

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true)
        setError('')
        const userData = await getProfile(id)
        setUser(userData)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load profile'
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [id])

  const handleChoosePicture = () => {
    fileInputRef.current?.click()
  }

  const handleProfilePictureSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''

    if (!file) {
      return
    }

    try {
      setUploadingPicture(true)
      setError('')
      setStatusMessage('')
      const updatedUser = await uploadProfilePicture(file)
      setUser(updatedUser)
      setPictureVersion((version) => version + 1)
      setStatusMessage('Profile picture updated.')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update profile picture'
      setError(message)
    } finally {
      setUploadingPicture(false)
    }
  }

  const handleRemovePicture = async () => {
    try {
      setUploadingPicture(true)
      setError('')
      setStatusMessage('')
      const updatedUser = await deleteProfilePicture()
      setUser(updatedUser)
      setPictureVersion((version) => version + 1)
      setStatusMessage('Profile picture removed.')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to remove profile picture'
      setError(message)
    } finally {
      setUploadingPicture(false)
    }
  }

  if (loading) {
    return <div className="Profile"><p>Loading profile...</p></div>
  }

  if (error) {
    return (
      <div className="Profile">
        <StatusMessage message={error} type="error" />
      </div>
    )
  }

  return (
    <div className="Profile">
      <div className="ProfileCard">
        <div className="ProfileImagePanel">
          <div className="profile-image" aria-hidden="true">
            {profilePictureSrc ? (
              <img src={profilePictureSrc} alt={`${user?.name || 'User'} profile`} />
            ) : (
              <span>{user?.name?.charAt(0).toUpperCase() || '?'}</span>
            )}
          </div>

          {isOwnProfile && (
            <div className="ProfilePictureActions">
              <input
                ref={fileInputRef}
                className="ProfilePictureInput"
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                onChange={handleProfilePictureSelected}
              />
              <Button onClick={handleChoosePicture} disabled={uploadingPicture}>
                {uploadingPicture ? 'Saving...' : 'Change Photo'}
              </Button>
              <Button
                onClick={handleRemovePicture}
                disabled={uploadingPicture || !user?.profile_picture_url}
                type="secondary"
              >
                Remove Photo
              </Button>
            </div>
          )}
        </div>

        <div className="profile-info">
          <p className="ProfileEyebrow">My Profile</p>
          <h1>{user?.name || 'Profile'}</h1>

          <StatusMessage message={statusMessage} type="success" />

          {user && <ProfileDetails profile={user} />}

          {isTeacher() && (
            <div className="ProfileActionRow">
            <Button onClick={() => navigate('/change-password')}>
              Change Password
            </Button>
          </div>
          )}
        </div>
      </div>
    </div>
  )
}