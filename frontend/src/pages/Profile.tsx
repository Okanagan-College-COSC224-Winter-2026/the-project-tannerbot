import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Profile.css'
import Button from '../components/Button'
import { isTeacher } from '../util/login'

interface UserData {
  id: number
  name: string
  email: string
  role: string
}

export default function Profile() {
  const navigate = useNavigate()
  const [user, setUser] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await fetch('http://localhost:5000/user/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        })

        if (!response.ok) {
          throw new Error(`Failed to fetch user data: ${response.status}`)
        }

        const userData = await response.json()
        setUser(userData)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load profile'
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [])

  if (loading) {
    return <div className="Profile"><p>Loading...</p></div>
  }

  if (error) {
    return <div className="Profile"><p style={{ color: 'red' }}>{error}</p></div>
  }

  return (
    <div className="Profile">
      <div className="profile-image">
        <img src={`https://placehold.co/200x200`} alt="profile" />
      </div>

      <div className="profile-info">
        <h1>Full Name</h1>
        <span>{user?.name || 'N/A'}</span>
        <h1>Email</h1>
        <span>{user?.email || 'N/A'}</span>
        
        {isTeacher() && (
          <div style={{ marginTop: '2rem' }}>
            <Button onClick={() => navigate('/change-password')}>
              Change Password
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}