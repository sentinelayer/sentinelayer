import React, { useEffect, useState } from 'react'

export const ConfigurationPage: React.FC = () => {
    const [config, setConfig] = useState<any>({})
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/configuration')
            .then(res => res.json())
            .then((data: any) => { setConfig(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading...</div>

    return (
        <div className="configuration-page">
            <h1>Configuration</h1>
            <div className="config-grid">
                {Object.entries(config).map(([key, value]) => (
                    <div key={key} className="config-item">
                        <span className="config-key">{key}</span>
                        <span className="config-value">{String(value)}</span>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default ConfigurationPage;
