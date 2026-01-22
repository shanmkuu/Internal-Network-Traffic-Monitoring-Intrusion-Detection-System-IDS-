import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Shield, Activity, ShieldAlert, Terminal, Settings2, LayoutGrid, HardDrive, Network } from 'lucide-react';

const Sidebar = () => {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Dashboard', icon: LayoutGrid },
        { path: '/network', label: 'Network Analytics', icon: Network },
        { path: '/live', label: 'Live Traffic', icon: Activity },
        { path: '/alerts', label: 'Security Alerts', icon: ShieldAlert },
        { path: '/logs', label: 'Logs', icon: HardDrive },
        { path: '/reports', label: 'Reports', icon: Terminal },
        { path: '/settings', label: 'Settings', icon: Settings2 },
    ];

    return (
        <aside className="hidden lg:flex flex-col w-64 h-screen fixed left-0 top-0 bg-[#0F172A] border-r border-gray-800 z-30">
            {/* Brand Header */}
            <div className="flex items-center gap-3 px-6 h-16 border-b border-gray-800">
                <Shield className="w-6 h-6 text-blue-500" />
                <h1 className="text-lg font-bold text-white tracking-wide">
                    CYBER<span className="text-blue-500">WATCH</span>
                </h1>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-6 space-y-1">
                <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Main Menu</p>

                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${isActive
                            ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.15)]'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {({ isActive }) => (
                            <>
                                <div className={`p-2 rounded-lg backdrop-blur-md border transition-all duration-300 ${isActive
                                    ? 'bg-blue-500/20 border-blue-400/30 shadow-inner shadow-blue-500/20'
                                    : 'bg-white/5 border-white/10 group-hover:bg-white/10 group-hover:border-white/20'
                                    }`}>
                                    <item.icon className="w-4 h-4" />
                                </div>
                                <span className="tracking-wide">{item.label}</span>
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Footer Info */}
            <div className="p-4 border-t border-gray-800">
                <div className="px-3 py-2 bg-[#1E293B] rounded-lg border border-gray-700">
                    <p className="text-xs text-gray-400">v2.4.0-enterprise</p>
                    <p className="text-[10px] text-gray-600 mt-1">Last update: Today</p>
                </div>
            </div>
        </aside >
    );
};

export default Sidebar;
