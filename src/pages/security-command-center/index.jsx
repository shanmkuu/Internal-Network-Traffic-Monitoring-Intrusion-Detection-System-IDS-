import React, { useEffect, useState } from 'react';
import { Shield, Siren, Zap, Cpu, ArrowUp, ArrowDown, ExternalLink, Activity, Server } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { api } from '../../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { format } from 'date-fns';

const SummaryCard = ({ title, value, subtext, icon: Icon, color, trend }) => (
    <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700 hover:border-blue-500/50 transition-all duration-300 group">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-xl backdrop-blur-md border border-white/10 shadow-inner ${color.replace('bg-', 'bg-')}/20 group-hover:scale-110 transition-all duration-300 relative overflow-hidden`}>
                <div className={`absolute inset-0 ${color} opacity-10 blur-xl`}></div>
                <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')} relative z-10 drop-shadow-md`} />
            </div>
        </div>
        <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
        <div className="flex items-baseline gap-2 mt-1">
            <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
            <span className="text-xs text-gray-500">{subtext}</span>
        </div>
    </div>
);

const SecurityCommandCenter = () => {
    const [stats, setStats] = useState(null);
    const [history, setHistory] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [statsData, historyData, alertsData, statusData] = await Promise.all([
                api.getStats(),
                api.getHistory(50),
                api.getAlerts(),
                api.getStatus()
            ]);

            if (statsData && statsData.length > 0) setStats(statsData[0]);
            setHistory(historyData);
            setAlerts(alertsData || []);
            if (statusData && statusData.length > 0) setStatus(statusData[0]);
        } catch (error) {
            console.error("Error fetching dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    // Derived Metrics
    const highSeverityCount = alerts.filter(a => a.severity === 'High').length;
    const totalPackets = stats?.total_packets || 0;

    // Protocol Distribution Data for Pie Chart
    const protocolData = stats ? [
        { name: 'TCP', value: stats.tcp_packets, color: '#3B82F6' },
        { name: 'UDP', value: stats.udp_packets, color: '#8B5CF6' },
        { name: 'ICMP', value: stats.icmp_packets, color: '#F59E0B' },
        { name: 'HTTP', value: stats.http_packets || 0, color: '#10B981' },
        { name: 'HTTPS', value: stats.https_packets || 0, color: '#EC4899' },
        { name: 'DNS', value: stats.dns_packets || 0, color: '#6366F1' },
    ].filter(d => d.value > 0) : [];

    return (
        <div className="space-y-6">
            {/* Title Area */}
            <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Security Command Center</h1>
                <p className="text-gray-400 text-sm">System Overview & Threat Intelligence</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <SummaryCard
                    title="Total Traffic"
                    value={totalPackets.toLocaleString()}
                    subtext="packets detected"
                    icon={Zap}
                    color="bg-blue-500"
                />
                <SummaryCard
                    title="Suspicious Events"
                    value={alerts.length}
                    subtext="Recent Alerts"
                    icon={Siren}
                    color="bg-amber-500"
                />
                <SummaryCard
                    title="Critical Threats"
                    value={highSeverityCount}
                    subtext="High Severity"
                    icon={Shield}
                    color="bg-red-500"
                />
                <SummaryCard
                    title="System Status"
                    value={status?.status || 'Unknown'}
                    subtext={`Interface: ${status?.monitored_interface || 'All'}`}
                    icon={Cpu}
                    color="bg-emerald-500"
                />
            </div>

            {/* Main Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Traffic Chart */}
                <div className="lg:col-span-2 bg-[#1E293B] rounded-xl border border-gray-700 p-6">
                    <h3 className="text-white font-bold mb-6 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-blue-500" /> Network Traffic Overview
                    </h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={history}>
                                <defs>
                                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                                <XAxis
                                    dataKey="created_at"
                                    tick={false}
                                    stroke="#9CA3AF"
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#9CA3AF"
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#fff', borderRadius: '0.5rem' }}
                                    itemStyle={{ color: '#E5E7EB' }}
                                    labelStyle={{ color: '#9CA3AF', marginBottom: '0.5rem' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="total_packets"
                                    stroke="#3B82F6"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorTotal)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Protocol Distribution */}
                <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-6">
                    <h3 className="text-white font-bold mb-6 flex items-center gap-2">
                        <Server className="w-5 h-5 text-purple-500" /> Protocol Distribution
                    </h3>
                    <div className="h-64 flex flex-col items-center justify-center">
                        {protocolData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={protocolData}
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {protocolData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#fff', borderRadius: '0.5rem' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-gray-500">No data available</div>
                        )}
                        <div className="flex gap-4 mt-4">
                            {protocolData.map(p => (
                                <div key={p.name} className="flex items-center gap-1 text-xs text-gray-400">
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }}></div>
                                    {p.name}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Alerts Table */}
            <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-6">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-white font-bold flex items-center gap-2">
                        <Shield className="w-5 h-5 text-red-500" /> Recent Security Alerts
                    </h3>
                    <NavLink to="/alerts" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
                        View All <ExternalLink className="w-3 h-3" />
                    </NavLink>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-400">
                        <thead className="text-xs uppercase bg-[#0F172A] text-gray-500">
                            <tr>
                                <th className="px-4 py-3 rounded-l-lg">Time</th>
                                <th className="px-4 py-3">Severity</th>
                                <th className="px-4 py-3">Type</th>
                                <th className="px-4 py-3 rounded-r-lg">Source</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700">
                            {alerts.slice(0, 5).map((alert) => (
                                <tr key={alert.id} className="hover:bg-[#0F172A]/50 transition-colors">
                                    <td className="px-4 py-3 font-mono">
                                        {format(new Date(alert.created_at), 'HH:mm:ss')}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${alert.severity === 'High' ? 'bg-red-500/10 text-red-500' :
                                            alert.severity === 'Medium' ? 'bg-amber-500/10 text-amber-500' :
                                                'bg-emerald-500/10 text-emerald-500'
                                            }`}>
                                            {alert.severity}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-white">{alert.alert_type}</td>
                                    <td className="px-4 py-3 font-mono">{alert.source_ip}</td>
                                </tr>
                            ))}
                            {alerts.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="text-center py-4 text-gray-500">No alerts detected</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default SecurityCommandCenter;