import React from 'react'

interface SecurityStatusProps {
  waf: string
  rateLimit: string
  auth: string
  tenant: string
}

export const SecurityStatus: React.FC<SecurityStatusProps> = ({ waf, rateLimit, auth, tenant }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', padding: '1rem' }}>
      <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
        <h4>WAF</h4>
        <p style={{ color: waf === 'active' ? 'green' : 'red' }}>{waf}</p>
      </div>
      <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
        <h4>Rate Limit</h4>
        <p style={{ color: rateLimit === 'active' ? 'green' : 'red' }}>{rateLimit}</p>
      </div>
      <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
        <h4>Auth</h4>
        <p style={{ color: auth === 'active' ? 'green' : 'red' }}>{auth}</p>
      </div>
      <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
        <h4>Tenant</h4>
        <p style={{ color: tenant === 'active' ? 'green' : 'red' }}>{tenant}</p>
      </div>
    </div>
  )
}
