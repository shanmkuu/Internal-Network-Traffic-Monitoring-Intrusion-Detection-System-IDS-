import React, { useEffect, useState } from 'react';
import { Shield, Siren, Zap, Cpu, Activity, Server, ExternalLink, TrendingUp } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { api } from '../../services/api';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import { format } from 'date-fns';

/* ── Animated KPI Tile ────────────────────────────────────────────────── */
const StatCard = ({ title, value, subtext, icon: Icon, color, glow, delay = 0 }) => (
    <div
        className="stat-card"
        style={{ animationDelay: `${delay}ms` }}
    >
        {/* Diagonal gradient overlay */}
        <div
            style={{
                position: 'absolute', inset: 0, pointerEvents: 'none',
                background: `linear-gradient(135deg, ${color}0A 0%, transparent 60%)`,
                borderRadius: 12,
            }}
        />
        {/* Top accent strip */}
        <div style={{
            position: 'absolute', top: 0, left: '20%', right: '20%',
            height: 1,
            background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
            opacity: 0.6,
        }} />

        <div className="stat-card-icon" style={{ background: `${color}14`, borderColor: `${color}25`, boxShadow: `0 0 12px ${color}20` }}>
            <Icon className="w-4 h-4" style={{ color }} strokeWidth={1.75} />
        </div>
        <div className="stat-card-label">{title}</div>
        <div className="stat-card-value" style={glow ? { textShadow: `0 0 20px ${color}60` } : {}}>
            {value}
        </div>
        <div className="stat-card-sub">{subtext}</div>
    </div>
);

/* ── Custom Chart Tooltip ─────────────────────────────────────────────── */
const AuroraTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
        <div style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-glow)',
            borderRadius: 8,
            padding: '8px 12px',
            fontSize: 11,
            fontFamily: "'Space Mono', monospace",
            boxShadow: '0 0 16px rgba(124,58,237,0.2)',
        }}>
            <p style={{ color: 'var(--neon-primary)' }}>{payload[0]?.value?.toLocaleString()} pkts</p>
        </div>
    );
};

/* ── Main ────────────────────────────────────────────────────────────── */
const SecurityCommandCenter = () => {
    const [stats, setStats] = useState(null);
    const [history, setHistory] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [statsData, historyData, alertsData, statusData] = await Promise.all([
                api.getStats(), api.getHistory(60), api.getAlerts(), api.getStatus(),
            ]);
            if (statsData?.length > 0) setStats(statsData[0]);
            setHistory(historyData);
            setAlerts(alertsData || []);
            if (statusData?.length > 0) setStatus(statusData[0]);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    useEffect(() => {
        fetchData();
        const id = setInterval(fetchData, 5000);
        return () => clearInterval(id);
    }, []);

    const highSeverityCount = alerts.filter(a => a.alert?.severity === 1).length;
    const totalPackets = stats?.total_packets || 0;

    // Aurora-toned protocol donut
    const protocolData = stats ? [
        { name: 'TCP', value: stats.tcp_packets, color: '#7C3AED' },
        { name: 'UDP', value: stats.udp_packets, color: '#06B6D4' },
        { name: 'ICMP', value: stats.icmp_packets, color: '#A78BFA' },
        { name: 'HTTP', value: stats.http_packets || 0, color: '#10B981' },
        { name: 'HTTPS', value: stats.https_packets || 0, color: '#34D399' },
        { name: 'DNS', value: stats.dns_packets || 0, color: '#2DD4BF' },
    ].filter(d => d.value > 0) : [];

    const sevMap = { 1: 'High', 2: 'Medium', 3: 'Low' };
    const sevClass = { High: 'sev sev-high', Medium: 'sev sev-medium', Low: 'sev sev-low' };

    return (
        <div className="space-y-5">

            {/* ── Page Title ─────────────────────────────────────────────── */}
            <div className="flex items-center justify-between animate-float-up">
                <div>
                    <h1 className="text-xl font-bold aurora-text">Security Command Center</h1>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-dim)' }}>
                        Real-time threat intelligence & network analysis
                    </p>
                </div>
                <div className="badge badge-online">
                    <span className="live-dot" style={{ width: 5, height: 5 }} />
                    {loading ? 'Syncing…' : 'Live'}
                </div>
            </div>

            {/* ── KPI Cards ──────────────────────────────────────────────── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Total Traffic" value={totalPackets.toLocaleString()} subtext="packets detected" icon={Zap} color="#A78BFA" delay={0} />
                <StatCard title="Suspicious Events" value={alerts.length} subtext="recent alerts" icon={Siren} color="#FBBF24" delay={60} />
                <StatCard title="Critical Threats" value={highSeverityCount} subtext="high severity" icon={Shield} color={highSeverityCount > 0 ? '#F43F5E' : '#475569'} glow={highSeverityCount > 0} delay={120} />
                <StatCard title="System Status" value={status?.status || 'Unknown'} subtext={`iface: ${status?.monitored_interface || 'all'}`} icon={Cpu} color="#10B981" delay={180} />
            </div>

            {/* ── Charts Row ─────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                {/* Traffic Sparkline */}
                <div className="m-panel lg:col-span-2 animate-float-up" style={{ animationDelay: '100ms' }}>
                    <div className="m-panel-header">
                        <div className="m-panel-title">
                            <Activity className="w-3.5 h-3.5" style={{ color: 'var(--neon-primary)' }} strokeWidth={1.75} />
                            Network Traffic
                        </div>
                        <span className="mono text-[10px]" style={{ color: 'var(--text-dim)' }}>
                            {history.length} samples · 5s interval
                        </span>
                    </div>
                    <div className="m-panel-body pt-2">
                        <div style={{ height: 220 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={history} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="auroraGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#7C3AED" stopOpacity={0.3} />
                                            <stop offset="60%" stopColor="#06B6D4" stopOpacity={0.1} />
                                            <stop offset="100%" stopColor="#7C3AED" stopOpacity={0} />
                                        </linearGradient>
                                        <filter id="glow">
                                            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                                            <feMerge>
                                                <feMergeNode in="coloredBlur" />
                                                <feMergeNode in="SourceGraphic" />
                                            </feMerge>
                                        </filter>
                                    </defs>
                                    <CartesianGrid strokeDasharray="2 6" stroke="rgba(167,139,250,0.06)" vertical={false} />
                                    <XAxis dataKey="created_at" tick={false} axisLine={false} tickLine={false} />
                                    <YAxis
                                        tick={{ fontSize: 10, fill: '#475569', fontFamily: "'Space Mono'" }}
                                        axisLine={false} tickLine={false}
                                    />
                                    <Tooltip content={<AuroraTooltip />} cursor={{ stroke: 'rgba(167,139,250,0.2)', strokeWidth: 1 }} />
                                    <Area
                                        type="monotone"
                                        dataKey="total_packets"
                                        stroke="url(#auroraLineGrad)"
                                        strokeWidth={1.5}
                                        fill="url(#auroraGrad)"
                                        dot={false}
                                        activeDot={{ r: 4, fill: '#A78BFA', stroke: '#7C3AED', strokeWidth: 1 }}
                                        filter="url(#glow)"
                                    />
                                    <defs>
                                        <linearGradient id="auroraLineGrad" x1="0" y1="0" x2="1" y2="0">
                                            <stop offset="0%" stopColor="#7C3AED" />
                                            <stop offset="50%" stopColor="#06B6D4" />
                                            <stop offset="100%" stopColor="#10B981" />
                                        </linearGradient>
                                    </defs>
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Protocol Donut */}
                <div className="m-panel animate-float-up" style={{ animationDelay: '150ms' }}>
                    <div className="m-panel-header">
                        <div className="m-panel-title">
                            <Server className="w-3.5 h-3.5" style={{ color: 'var(--aurora-cyan)' }} strokeWidth={1.75} />
                            Protocol Mix
                        </div>
                    </div>
                    <div className="m-panel-body flex flex-col items-center">
                        {protocolData.length > 0 ? (
                            <>
                                <div style={{ height: 160, width: '100%' }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <defs>
                                                {protocolData.map((p, i) => (
                                                    <filter key={i} id={`glow-${i}`}>
                                                        <feGaussianBlur stdDeviation="3" result="blur" />
                                                        <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                                                    </filter>
                                                ))}
                                            </defs>
                                            <Pie
                                                data={protocolData}
                                                innerRadius={45}
                                                outerRadius={65}
                                                paddingAngle={4}
                                                dataKey="value"
                                                stroke="none"
                                                startAngle={90}
                                                endAngle={-270}
                                            >
                                                {protocolData.map((entry, i) => (
                                                    <Cell
                                                        key={i}
                                                        fill={entry.color}
                                                        opacity={0.9}
                                                        style={{ filter: `drop-shadow(0 0 4px ${entry.color})` }}
                                                    />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{
                                                    background: 'var(--bg-elevated)',
                                                    border: '1px solid var(--border-glow)',
                                                    borderRadius: 8,
                                                    fontSize: 11,
                                                    fontFamily: "'Space Mono'",
                                                    color: 'var(--text-primary)',
                                                }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="w-full mt-1 space-y-1.5">
                                    {protocolData.map(p => (
                                        <div key={p.name} className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className="w-1.5 h-1.5 rounded-full" style={{ background: p.color, boxShadow: `0 0 4px ${p.color}` }} />
                                                <span className="text-[11px]" style={{ color: 'var(--text-secondary)' }}>{p.name}</span>
                                            </div>
                                            <span className="mono text-[11px]" style={{ color: 'var(--text-dim)' }}>
                                                {p.value?.toLocaleString()}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-40 gap-2">
                                <TrendingUp className="w-6 h-6" style={{ color: 'var(--text-dim)' }} strokeWidth={1} />
                                <p className="text-xs" style={{ color: 'var(--text-dim)' }}>Awaiting traffic data</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Alerts Table ───────────────────────────────────────────── */}
            <div className="m-panel animate-float-up" style={{ animationDelay: '200ms' }}>
                <div className="m-panel-header">
                    <div className="m-panel-title">
                        <Shield
                            className="w-3.5 h-3.5"
                            style={{ color: highSeverityCount > 0 ? 'var(--neon-danger)' : 'var(--neon-primary)' }}
                            strokeWidth={1.75}
                        />
                        Recent Security Alerts
                        {highSeverityCount > 0 && (
                            <span className="sev sev-high ml-1">{highSeverityCount} critical</span>
                        )}
                    </div>
                    <NavLink to="/alerts" className="btn btn-ghost text-[11px]" style={{ padding: '3px 10px' }}>
                        View all <ExternalLink className="w-3 h-3" strokeWidth={1.75} />
                    </NavLink>
                </div>
                <table className="ids-table">
                    <thead>
                        <tr>
                            {['Time', 'Severity', 'Category', 'Source IP'].map(col => (
                                <th key={col} style={{ textAlign: 'left' }}>{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {alerts.slice(0, 6).map((alert, i) => {
                            const severity = sevMap[alert.alert?.severity] || 'Low';
                            return (
                                <tr key={alert._original_id || i}>
                                    <td className="mono" style={{ color: 'var(--text-secondary)' }}>
                                        {alert.timestamp ? format(new Date(alert.timestamp), 'HH:mm:ss') : '—'}
                                    </td>
                                    <td><span className={sevClass[severity]}>{severity}</span></td>
                                    <td style={{ color: 'var(--text-primary)' }}>{alert.alert?.category || 'Unknown'}</td>
                                    <td className="mono" style={{ color: 'var(--text-secondary)' }}>{alert.src_ip || '—'}</td>
                                </tr>
                            );
                        })}
                        {alerts.length === 0 && (
                            <tr>
                                <td colSpan="4" style={{ textAlign: 'center', padding: '28px 0', color: 'var(--text-dim)' }}>
                                    ✓ No threat events detected
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default SecurityCommandCenter;