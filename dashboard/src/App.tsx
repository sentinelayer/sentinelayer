import React, { useState } from 'react';
import Login from './components/Login';
import SecurityDashboard from './components/SecurityDashboard';

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);

  const handleLogin = (token: string, tenantId: string) => {
    setToken(token);
    setTenantId(tenantId);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="App">
      <header>
        <h1>SentinelLayer</h1>
        <span>Tenant: {tenantId}</span>
      </header>
      <SecurityDashboard />
    </div>
  );
}

export default App;
