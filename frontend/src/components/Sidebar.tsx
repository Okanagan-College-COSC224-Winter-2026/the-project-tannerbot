import { hasRole, logout } from '../util/login'
import './Sidebar.css'

export default function Sidebar() {
  const location = window.location.pathname

  return (
    <div className="Sidebar">
      <div className="SidebarLogo">
        <img src="/oc_logo.png" alt="OC Logo" />
      </div>

      <div className="SidebarTop">
        <SidebarRow
          onClick={() => logout()}
          href='#'
          selected={false}
        >
          Logout
        </SidebarRow>

        <SidebarRow selected={location === '/home'} href="/home">
          Home
        </SidebarRow>

        {hasRole('student', 'teacher', 'admin') ? (
          <SidebarRow selected={location === '/courses/search'} href="/courses/search">
            Search Courses
          </SidebarRow>
        ) : null}
        
        <SidebarRow selected={location.includes('/profile')} href="/profile">
          Profile
        </SidebarRow>
      </div>
    </div>
  )
}

interface SidebarRowProps {
  selected: boolean
  href: string
  children: React.ReactNode
  onClick?: () => void
}

function SidebarRow(props: SidebarRowProps) {
  return (
    <div className={`SidebarRow ${props.selected ? 'selected' : ''}`} onClick={props.onClick}>
      <a href={props.selected ? '#' : props.href}>{props.children}</a>
    </div>
  )
}