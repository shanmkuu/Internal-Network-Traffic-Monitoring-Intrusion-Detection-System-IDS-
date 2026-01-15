import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { format } from 'date-fns';

const AlertTable = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchAlerts = async () => {
        try {
            const data = await api.getAlerts();
            setAlerts(data);
        } catch (err) {
            setError('Failed to load alerts');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAlerts();
        // Refresh every 5 seconds for "real-time" feel
        const interval = setInterval(fetchAlerts, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="text-center p-4">Loading alerts...</div>;
    if (error) return <div className="text-center text-red-500 p-4">{error}</div>;

    return (
        <div className="overflow-x-auto bg-[#1A2332] rounded-2xl">
            <table className="min-w-full text-left text-sm whitespace-nowrap">
                <thead className="uppercase tracking-wider border-b border-white/5 bg-[#243447] text-gray-400">
                    <tr>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Time</th>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Severity</th>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Type</th>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Source IP</th>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Destination IP</th>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Protocol</th>
                        <th scope="col" className="px-6 py-4 font-mono font-medium">Description</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                    {alerts.map((alert) => (
                        <tr key={alert.id} className="hover:bg-white/5 transition-colors">
                            <td className="px-6 py-4 text-gray-300 font-mono">
                                {format(new Date(alert.created_at), 'HH:mm:ss')}
                            </td>
                            <td className="px-6 py-4">
                                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-bold rounded-md border border-opacity-20
                  ${alert.severity === 'High' ? 'bg-red-500/10 text-red-500 border-red-500' :
                                        alert.severity === 'Medium' ? 'bg-amber-500/10 text-amber-500 border-amber-500' :
                                            'bg-emerald-500/10 text-emerald-500 border-emerald-500'}`}>
                                    {alert.severity}
                                </span>
                            </td>
                            <td className="px-6 py-4 text-white font-medium">{alert.alert_type}</td>
                            <td className="px-6 py-4 font-mono text-gray-400">{alert.source_ip}</td>
                            <td className="px-6 py-4 font-mono text-gray-400">{alert.destination_ip}</td>
                            <td className="px-6 py-4 text-gray-300">
                                <span className="px-2 py-1 bg-white/5 rounded text-xs font-mono">{alert.protocol}</span>
                            </td>
                            <td className="px-6 py-4 text-gray-400 max-w-xs truncate" title={alert.description}>
                                {alert.description}
                            </td>
                        </tr>
                    ))}
                    {alerts.length === 0 && (
                        <tr>
                            <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                                <div className="flex flex-col items-center gap-2">
                                    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center">
                                        <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                    </div>
                                    <p>No active security alerts</p>
                                </div>
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default AlertTable;