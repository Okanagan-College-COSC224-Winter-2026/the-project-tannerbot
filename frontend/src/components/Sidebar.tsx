import { hasRole, logout } from '../util/login'
import { NavLink } from 'react-router-dom'
import './Sidebar.css'

export default function Sidebar() {
  return (
    <aside className="Sidebar d-flex flex-column border-end px-3 py-4">
      <div className="SidebarLogo text-center mb-4">
        <img src="/oc_logo.png" alt="OC Logo" className="img-fluid" />
      </div>

      <div className="d-grid mb-3">
        <button type="button" className="btn btn-outline-secondary" onClick={() => logout()}>
          Logout
        </button>
      </div>

      <nav className="nav nav-pills flex-column gap-2">
        <SidebarRow href="/home">Home</SidebarRow>

        {hasRole('student', 'teacher', 'admin') ? (
          <SidebarRow href="/courses/search">Search Courses</SidebarRow>
        ) : null}

        { /* TODO: make this ID match who is logged in */ }
        <SidebarRow href="/profile/1">My Info</SidebarRow>
      </nav>
    </aside>
  )
}

interface SidebarRowProps {
  href: string
  children: React.ReactNode
}

function SidebarRow(props: SidebarRowProps) {
  return (
    <NavLink
      to={props.href}
      className={({ isActive }) =>
        `SidebarRow nav-link px-3 py-2 rounded-3 ${isActive ? 'active' : 'text-dark'}`
      }
      end={props.href === '/home'}
    >
      {props.children}
    </NavLink>
  )
}