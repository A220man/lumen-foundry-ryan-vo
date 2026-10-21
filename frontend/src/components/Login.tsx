import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleDemoLogin = async () => {
    setLoading(true);
    setError('');
    try {
      // Demo mode: create a mock JWT token
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({
        sub: 'demo-user',
        email: 'demo@lumen-foundry.local',
        preferred_username: 'demo',
        name: 'Demo User',
        realm_access: { roles: ['viewer', 'operator'] },
        exp: Math.floor(Date.now() / 1000) + 3600,
        iat: Math.floor(Date.now() / 1000),
      }));
      const signature = btoa('demo-signature');
      const token = `${header}.${payload}.${signature}`;
      
      login(token, {
        id: 'demo-user',
        email: 'demo@lumen-foundry.local',
        name: 'Demo User',
        roles: ['viewer', 'operator'],
      });
      
      navigate('/dashboard');
    } catch (err) {
      setError('Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      // In a real app, this would call Keycloak/OIDC
      // For demo, we simulate a successful login
      await new Promise(r => setTimeout(r, 500));
      
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify({
        sub: 'user-123',
        email,
        preferred_username: email.split('@')[0],
        name: email.split('@')[0],
        realm_access: { roles: ['viewer', 'operator'] },
        exp: Math.floor(Date.now() / 1000) + 3600,
        iat: Math.floor(Date.now() / 1000),
      }));
      const signature = btoa('signature');
      const token = `${header}.${payload}.${signature}`;
      
      login(token, {
        id: 'user-123',
        email,
        name: email.split('@')[0],
        roles: ['viewer', 'operator'],
      });
      
      navigate('/dashboard');
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">L</div>
          <h1>Lumen Foundry</h1>
          <p>High-throughput LLM Inference Engine</p>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="login-divider">
          <span>or</span>
        </div>

        <button className="btn btn-outline btn-block" onClick={handleDemoLogin} disabled={loading}>
          🎮 Continue as Demo User
        </button>

        <div className="login-footer">
          <p>Demo mode: any credentials work. No real authentication in development.</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
