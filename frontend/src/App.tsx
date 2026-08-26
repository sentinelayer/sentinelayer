import React from 'react';
import SecurityDashboard from './components/SecurityDashboard';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>SentinelLayer</h1>
        <p>API Security Platform</p>
      </header>
      <main>
        <SecurityDashboard />
      </main>
    </div>
  );
}

export default App;
