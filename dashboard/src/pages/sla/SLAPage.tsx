import React, { useEffect, useState } from 'react'

export const SLAPage: React.FC = () => {
    const [sla, setSla] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetch('/api/v1/sla/report')
            .then(res => res.json())
            .then((data: any) => { setSla(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    if (loading) return <div>Loading SLA...</div>
    return (
        <div>
            <h1>SLA Report</h1>
            {sla && (
                <div>
                    <p>Compliance Rate: {sla.compliance_rate || 0}%</p>
                    <p>Period: {sla.period_hours || 24} hours</p>
                    <p>Pass: {sla.pass_count || 0}</p>
                    <p>Fail: {sla.fail_count || 0}</p>
                </div>
            )}
        </div>
    )
}

export default SLAPage;
