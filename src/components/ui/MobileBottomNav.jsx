import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, Activity, Bell, Globe } from 'lucide-react';

const navItems = [
    { id: 'security', icon: Shield, label: 'Command', path: '/' },
    { id: 'network', icon: Globe, label: 'Network', path: '/network' },
    { id: 'alerts', icon: Bell, label: 'Alerts', path: '/alerts' },
    { id: 'live', icon: Activity, label: 'Live', path: '/live' },
];

const MobileBottomNav = () => {
    const navigate = useNavigate();
    const location = useLocation();

    return (
        <div
            className="fixed bottom-0 left-0 right-0 z-50 lg:hidden"
            style={{
                background: 'rgba(6,13,24,0.95)',
                backdropFilter: 'blur(16px)',
                borderTop: '1px solid var(--border-subtle)',
            }}
        >
            <div className="flex justify-around items-center h-16">
                {navItems.map(({ id, icon: Icon, label, path }) => {
                    const isActive = location.pathname === path;
                    return (
                        <button
                            key={id}
                            onClick={() => navigate(path)}
                            className="flex flex-col items-center justify-center w-full h-full gap-0.5 transition-all duration-200"
                            style={{ color: isActive ? 'var(--neon-primary)' : 'var(--text-dim)' }}
                        >
                            <div
                                style={{
                                    padding: '4px 10px',
                                    borderRadius: 8,
                                    background: isActive ? 'rgba(124,58,237,0.15)' : 'transparent',
                                    boxShadow: isActive ? '0 0 8px rgba(124,58,237,0.2)' : 'none',
                                    transition: 'all 200ms ease',
                                }}
                            >
                                <Icon size={18} strokeWidth={isActive ? 2 : 1.75} />
                            </div>
                            <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.04em' }}>{label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default MobileBottomNav;