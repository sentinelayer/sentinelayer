import React from 'react';

interface SecurityMetric {
  name: string;
  value: number;
  status: 'good' | 'warning' | 'critical';
}

const SecurityDashboard: React.FC = () => {
  const metrics: SecurityMetric[] = [
    { name: 'WAF Blocks', value: 156, status: 'good' },
    { name: 'Active Threats', value: 3, status: 'warning' },
    { name: 'Auth Failures', value: 45, status: 'critical' },
    { name: 'Risk Score', value: 12, status: 'good' },
  ];

  return (
    <div className="security-dashboard">
      <h1>SentinelLayer Security Dashboard</h1>
      <div className="metrics-grid">
        {metrics.map((metric) => (
          <div key={metric.name} className={`metric-card ${metric.status}`}>
            <h3>{metric.name}</h3>
            <p>{metric.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SecurityDashboard;
