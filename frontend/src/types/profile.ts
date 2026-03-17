export interface UserProfile {
  id: number
  name: string
  email: string
  role: string
  description: string | null
  profile_picture_url: string | null
}