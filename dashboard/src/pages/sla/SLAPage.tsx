import React, { useEffect, useState } from 'react'
import { apiGet } from '../../api/client'
import { LoadingSkeleton } from '../../components/LoadingSkeleton'

export const SLAPage: React.FC = () => {
    const [sla, setSla] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const controller = new AbortController()
        apiGet('/sla/report', { signal: controller.signal })
            .then((data: any) => { if (!controller.signal.aborted) setSla(data) })
            .catch(() => undefined)
            .finally(() => { if (!controller.signal.aborted) setLoading(false) })
        return () => controller.abort()
    }, [])

    if (loading) return <LoadingSkeleton label="Loading SLA report" />
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
