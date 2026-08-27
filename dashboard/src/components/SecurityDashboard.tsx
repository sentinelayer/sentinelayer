import React, { useEffect, useState } from 'react';
import { apiGet } from '../api/client';

interface Metric {
  name: string;
  value: number | string;
  status: 'good' | 'warning' | 'critical';
}

const SecurityDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Metric[]>('/metrics/security')
      .then((data) => {
        setMetrics(data);
        setError(null);
      })
      .catch(() => {
        setError('No data available - Please check backend');
        setMetrics([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading security metrics...</div>;
  if (error) return <div className="error">{error}</div>;
  if (metrics.length === 0) return <div>No metrics available</div>;

  return (
    <div className="security-dashboard">
      <h1>Security Dashboard</h1>
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
