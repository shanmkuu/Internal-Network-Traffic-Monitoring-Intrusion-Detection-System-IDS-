import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    Shield, Activity, ShieldAlert, Terminal,
    Settings2, LayoutGrid, HardDrive, Network, Wifi
} from 'lucide-react';

const navItems = [
    { path: '/', label: 'Command', icon: LayoutGrid, end: true },
    { path: '/network', label: 'Network', icon: Network },
    { path: '/live', label: 'Live Feed', icon: Activity },
    { path: '/alerts', label: 'Alerts', icon: ShieldAlert },
    { path: '/logs', label: 'Logs', icon: HardDrive },
    { path: '/reports', label: 'Reports', icon: Terminal },
    { path: '/settings', label: 'Settings', icon: Settings2 },
];

const Sidebar = () => (
    <aside className="ids-sidebar">
        {/* Brand */}
        <div className="ids-sidebar-brand">
            <div className="ids-brand-orb">
                <Shield className="w-4 h-4 text-white" strokeWidth={1.75} />
            </div>
            <span className="ids-brand-name">CyberWatch</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 overflow-y-auto">
            <div className="ids-nav-section">Navigation</div>
            {navItems.map(({ path, label, icon: Icon, end }) => (
                <NavLink
                    key={path}
                    to={path}
                    end={end}
                    className={({ isActive }) => `ids-nav-item ${isActive ? 'active' : ''}`}
                >
                    {({ isActive }) => (
                        <>
                            <div className="ids-nav-icon">
                                <Icon
                                    className="w-3.5 h-3.5"
                                    style={{ color: isActive ? 'var(--neon-primary)' : 'var(--text-dim)' }}
                                    strokeWidth={isActive ? 2 : 1.75}
                                />
                            </div>
                            <span>{label}</span>
                            {isActive && (
                                <span
                                    className="ml-auto w-1 h-4 rounded-full"
                                    style={{
                                        background: 'linear-gradient(to bottom, var(--aurora-violet), var(--aurora-cyan))',
                                        boxShadow: '0 0 4px var(--aurora-violet)',
                                    }}
                                />
                            )}
                        </>
                    )}
                </NavLink>
            ))}
        </nav>

        {/* System Status Footer */}
        <div className="px-3 py-4" style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <div
                className="px-3 py-2.5 rounded-lg flex items-center gap-2"
                style={{ background: 'rgba(167,139,250,0.05)', border: '1px solid var(--border-subtle)' }}
            >
                <Wifi className="w-3 h-3" style={{ color: 'var(--neon-secondary)' }} strokeWidth={1.75} />
                <div>
                    <p className="mono text-[10px]" style={{ color: 'var(--text-dim)' }}>v2.4.0-enterprise</p>
                    <p className="text-[9px]" style={{ color: 'var(--text-dim)' }}>IDS · Monitoring Active</p>
                </div>
                <span className="live-dot ml-auto" />
            </div>
        </div>
    </aside>
);

export default Sidebar;
