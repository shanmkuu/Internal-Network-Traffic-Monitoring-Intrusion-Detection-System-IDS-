import React, { useEffect, useState } from 'react';
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <h3 className="text-gray-400 text-sm font-medium">Total Packets</h3>
                <p className="text-2xl font-bold text-white mt-1">{stats.total_packets}</p>
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
    );
};

export default TrafficStats;
