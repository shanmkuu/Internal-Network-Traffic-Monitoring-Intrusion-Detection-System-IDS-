import React, { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';
import { api } from '../../../services/api';

const TrafficStats = () => {
    const [stats, setStats] = useState(null);

    const fetchStats = async () => {
        const data = await api.getStats();
        if (data && data.length > 0) {
            setStats(data[0]);
        }
    };

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 5000);
        return () => clearInterval(interval);
    }, []);

    if (!stats) return <div className="text-gray-500 text-center py-4">Waiting for traffic data...</div>;

    return (
        <div className="space-y-4 mb-6">
            <div className="flex justify-between items-end">
                <div className="text-xs text-gray-500 font-mono">
                    {stats ? (
                        <span>
                            Last updated: {new Date(stats.created_at).toLocaleTimeString()}
                            <span className="ml-2 opacity-50">
                                ({Math.floor((new Date() - new Date(stats.created_at)) / 1000)}s ago)
                            </span>
                        </span>
                    ) : 'Syncing...'}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Activity className="w-12 h-12 text-white" />
                    </div>
                    <h3 className="text-gray-400 text-sm font-medium z-10 relative">Total Packets (10s)</h3>
                    <p className="text-2xl font-bold text-white mt-1 z-10 relative">{stats.total_packets}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">TCP Packets</h3>
                    <p className="text-2xl font-bold text-blue-400 mt-1">{stats.tcp_packets}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">UDP Packets</h3>
                    <p className="text-2xl font-bold text-purple-400 mt-1">{stats.udp_packets}</p>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">ICMP Packets</h3>
                    <p className="text-2xl font-bold text-green-400 mt-1">{stats.icmp_packets}</p>
                </div>
            </div>
        </div>
    );
};

export default TrafficStats;
