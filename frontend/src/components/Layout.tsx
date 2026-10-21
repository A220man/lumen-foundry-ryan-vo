import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/models', label: 'Models', icon: '🤖' },
    { path: '/inference', label: 'Inference', icon: '⚡' },
  ];

  return (
    <div className="layout">
      <header className="header">
        <div className="header-brand">
          <NavLink to="/dashboard" className="brand-link">
            <span className="brand-icon">L</span>
            <span className="brand-text">Lumen Foundry</span>
          </NavLink>
        </div>
        <nav className="header-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="header-user">
          {user && (
            <>
              <span className="user-name">{user.name}</span>
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                Logout
              </button>
            </>
          )}
        </div>
      </header>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
