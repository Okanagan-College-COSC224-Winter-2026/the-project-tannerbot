import type { UserProfile } from '../types/profile'
import './ProfileDetails.css'

interface Props {
  profile: UserProfile
}

const labels: Array<{ key: keyof Pick<UserProfile, 'name' | 'email' | 'role'>; label: string }> = [
  { key: 'name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { key: 'role', label: 'Role' }
]

export default function ProfileDetails({ profile }: Props) {
  return (
    <div className="ProfileDetails" aria-label="Profile details">
      {labels.map(({ key, label }) => (
        <div className="ProfileDetailsRow" key={key}>
          <span className="ProfileDetailsLabel">{label}</span>
          <span className="ProfileDetailsValue">{profile[key]}</span>
        </div>
      ))}
    </div>
  )
}