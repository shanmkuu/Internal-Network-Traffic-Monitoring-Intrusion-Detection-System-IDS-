import React, { useState, useEffect, useRef } from 'react';
import { Wifi, Download, Pause, Square, Play, Box, Activity, Users, Share2, Server } from 'lucide-react';
import { api } from '../../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MetricCard = ({ icon: Icon, value, label, subval, color = "text-white" }) => (
    <div className="bg-[#1A2332] rounded-2xl p-6 border border-white/5 flex flex-col justify-between h-40 group hover:border-blue-500/30 transition-all duration-300">
        <div className={`p-3 rounded-xl backdrop-blur-md border border-white/10 w-fit ${color.replace('text-', 'bg-')}/10 group-hover:scale-110 transition-transform`}>
            <Icon className={`w-6 h-6 ${color}`} />
        </div>
        <div>
            <h3 className="text-4xl font-mono font-bold text-white mb-1 tracking-tighter shadow-blue-500/50 drop-shadow-sm">{value}</h3>
            <p className="text-gray-400 text-sm font-medium">{label}</p>
        </div>
    </div>
);

const LiveTrafficMonitor = () => {
    const [stats, setStats] = useState(null);
    const [history, setHistory] = useState([]);
    const [isRunning, setIsRunning] = useState(true);
    const [selectedProtocol, setSelectedProtocol] = useState('ALL');
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        if (!isRunning) return;

        try {
            const [currentStats, historyData] = await Promise.all([
                api.getStats(),
                api.getHistory(20)
            ]);

            if (currentStats && currentStats.length > 0) {
                setStats(currentStats[0]);
            }
            setHistory(historyData);
        } catch (error) {
            console.error("Failed to fetch live data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, [isRunning]);

    const handleExport = () => {
        const dataStr = JSON.stringify(history, null, 2);
        const blob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = "traffic_stats.json";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const toggleRunning = () => setIsRunning(!isRunning);
    const stopRunning = () => setIsRunning(false);

    // Filter displayed stats based on selected protocol? 
    // The main stats are cumulative, so filtering might not make sense unless we show specific counters.
    // We can use the buttons to highlight specific lines in the chart.

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-2xl font-mono font-bold text-white">Live Traffic Monitor</h1>
                <div className="flex gap-4">
                    <div className="flex items-center gap-3 px-4 py-2 bg-[#1A2332] rounded-xl border border-white/5 backdrop-blur-sm">
                        <div className={`w-10 h-10 rounded-xl backdrop-blur-md border border-white/10 flex items-center justify-center shadow-inner ${isRunning ? 'bg-emerald-500/10 shadow-emerald-500/20' : 'bg-red-500/10 shadow-red-500/20'}`}>
                            <Wifi className={`w-5 h-5 ${isRunning ? 'text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'text-red-500'}`} />
                        </div>
                        <div className="text-right">
                            <p className="text-xs font-bold text-white">{isRunning ? 'Connected' : 'Paused'}</p>
                            <p className="text-[10px] text-gray-500">{loading ? 'Loading...' : 'Live Stream'}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-6 py-2 bg-[#1A2332] hover:bg-[#253246] rounded-xl border border-white/5 text-white font-medium transition-colors"
                    >
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                </div>
            </div>

            {/* Control Grid */}
            <div className="grid grid-cols-12 gap-6">
                {/* Protocol Filters */}
                <div className="col-span-12 lg:col-span-5">
                    <div className="bg-[#1A2332] rounded-2xl p-6 border border-white/5">
                        <div className="grid grid-cols-3 gap-3">
                            {['TCP', 'UDP', 'ICMP', 'HTTPS', 'DNS', 'HTTP', 'DHCP'].map(proto => (
                                <button
                                    key={proto}
                                    onClick={() => setSelectedProtocol(proto === selectedProtocol ? 'ALL' : proto)}
                                    className={`h-24 rounded-xl flex flex-col items-center justify-center gap-2 font-bold hover:scale-105 transition-all duration-300 backdrop-blur-md border
                                        ${selectedProtocol === proto
                                            ? 'ring-2 ring-white/50 shadow-[0_0_20px_rgba(255,255,255,0.1)]'
                                            : 'border-white/5 hover:border-white/20'
                                        }
                                        ${proto === 'TCP' ? 'bg-blue-600/20 text-blue-400 border-blue-500/30' :
                                            proto === 'UDP' ? 'bg-purple-600/20 text-purple-400 border-purple-500/30' :
                                                proto === 'ICMP' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                                                    proto === 'HTTPS' ? 'bg-pink-600/20 text-pink-400 border-pink-500/30' :
                                                        proto === 'DNS' ? 'bg-indigo-600/20 text-indigo-400 border-indigo-500/30' :
                                                            'bg-[#243447]/50 text-gray-400'
                                        }`}
                                >
                                    {proto === 'TCP' && <Share2 className="w-5 h-5" />}
                                    {proto === 'UDP' && <Wifi className="w-5 h-5" />}
                                    {proto === 'ICMP' && <Activity className="w-5 h-5" />}
                                    {proto === 'HTTPS' && <Activity className="w-5 h-5" />}
                                    {proto === 'HTTP' && <Box className="w-5 h-5" />}
                                    {proto === 'DNS' && <Server className="w-5 h-5" />}
                                    {proto === 'DHCP' && <Share2 className="w-5 h-5" />}
                                    {proto}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Controls */}
                <div className="col-span-12 lg:col-span-7 flex flex-col gap-6">
                    <div className="flex gap-4">
                        <button
                            onClick={toggleRunning}
                            className={`${isRunning ? 'bg-amber-500 hover:bg-amber-600' : 'bg-emerald-500 hover:bg-emerald-600'} text-white px-8 py-4 rounded-xl font-bold flex items-center gap-2 shadow-lg transition-all`}
                        >
                            {isRunning ? <><Pause className="w-5 h-5 fill-current" /> Pause</> : <><Play className="w-5 h-5 fill-current" /> Resume</>}
                        </button>
                        <button
                            onClick={stopRunning}
                            className="bg-red-500 hover:bg-red-600 text-white px-8 py-4 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-red-500/20 transition-all"
                        >
                            <Square className="w-5 h-5 fill-current" /> Stop
                        </button>
                        <div className="bg-[#1A2332] px-8 py-4 rounded-xl border border-white/5 flex items-center gap-3 text-white font-bold ml-auto backdrop-blur-sm">
                            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-emerald-500 shadow-[0_0_15px_#10B981] animate-pulse' : 'bg-gray-500'}`}></div>
                            {isRunning ? 'Running' : 'Stopped'}
                        </div>
                    </div>

                    {/* Stats Summary */}
                    <div className="bg-[#1A2332] flex-1 rounded-2xl p-6 border border-white/5 relative overflow-hidden flex items-center justify-around">
                        <div className="text-center">
                            <h3 className="text-gray-400 text-sm">Total Packets</h3>
                            <p className="text-3xl font-mono font-bold text-white">{stats?.total_packets || 0}</p>
                        </div>
                        <div className="text-center">
                            <h3 className="text-gray-400 text-sm">TCP</h3>
                            <p className="text-3xl font-mono font-bold text-blue-500">{stats?.tcp_packets || 0}</p>
                        </div>
                        <div className="text-center">
                            <h3 className="text-gray-400 text-sm">UDP</h3>
                            <p className="text-3xl font-mono font-bold text-purple-500">{stats?.udp_packets || 0}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Metric Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard icon={Box} value={stats?.total_packets || 0} label="Total Packets" color="text-blue-500" />
                <MetricCard icon={Activity} value={stats?.tcp_packets || 0} label="TCP Flows" color="text-purple-500" />
                <MetricCard icon={Users} value={stats?.udp_packets || 0} label="UDP Flows" color="text-emerald-500" />
                <MetricCard icon={Share2} value={stats?.icmp_packets || 0} label="ICMP Events" color="text-amber-500" />
            </div>

            {/* Monitoring Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-96">
                <div className="lg:col-span-2 bg-[#1A2332] rounded-2xl p-6 border border-white/5 flex flex-col">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 backdrop-blur-sm shadow-inner shadow-emerald-500/10">
                            <Activity className="w-5 h-5 text-emerald-500" />
                        </div>
                        <h3 className="font-bold text-white">Live Traffic Flow</h3>
                    </div>
                    <div className="flex-1 min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={history}>
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
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'TCP') && (
                                    <Line type="monotone" dataKey="tcp_packets" stroke="#3B82F6" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'UDP') && (
                                    <Line type="monotone" dataKey="udp_packets" stroke="#8B5CF6" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'ICMP') && (
                                    <Line type="monotone" dataKey="icmp_packets" stroke="#F59E0B" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'HTTP') && (
                                    <Line type="monotone" dataKey="http_packets" stroke="#10B981" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'HTTPS') && (
                                    <Line type="monotone" dataKey="https_packets" stroke="#EC4899" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'DNS') && (
                                    <Line type="monotone" dataKey="dns_packets" stroke="#6366F1" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                                {(selectedProtocol === 'ALL' || selectedProtocol === 'DHCP') && (
                                    <Line type="monotone" dataKey="dhcp_packets" stroke="#F97316" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                )}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-[#1A2332] rounded-2xl p-6 border border-white/5 overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 backdrop-blur-sm shadow-inner shadow-blue-500/10">
                                <Share2 className="w-5 h-5 text-blue-400" />
                            </div>
                            <h3 className="font-bold text-white">Capture Stream</h3>
                        </div>
                        <span className="text-xs text-gray-500">Live</span>
                    </div>
                    <div className="space-y-2 overflow-y-auto flex-1 text-xs font-mono">
                        {history.slice().reverse().map((h, i) => (
                            <div key={i} className="p-2 bg-white/5 rounded-lg border border-white/5">
                                <span className="text-gray-400">{new Date(h.created_at).toLocaleTimeString()}</span>
                                <span className="mx-2 text-blue-400">Total: {h.total_packets}</span>
                                <span className="text-gray-500">TCP: {h.tcp_packets}</span>
                            </div>
                        ))}
                        {history.length === 0 && <div className="text-gray-500 text-center mt-10">Waiting for data...</div>}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LiveTrafficMonitor;