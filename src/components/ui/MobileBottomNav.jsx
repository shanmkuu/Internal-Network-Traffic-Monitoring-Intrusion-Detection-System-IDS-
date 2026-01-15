import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, Activity, Bell, Globe } from 'lucide-react';

const MobileBottomNav = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const navItems = [
        { id: 'security', icon: Shield, label: 'Security', path: '/' },
        { id: 'network', icon: Globe, label: 'Network', path: '/network' },
        { id: 'alerts', icon: Bell, label: 'Alerts', path: '/alerts' },
        { id: 'live', icon: Activity, label: 'Live', path: '/live' },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 lg:hidden z-50">
            <div className="flex justify-around items-center h-16">
                {navItems.map(({ id, icon: Icon, label, path }) => {
                    const isActive = location.pathname === path;
                    return (
                        <button
                            key={id}
                            onClick={() => navigate(path)}
                            className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isActive ? 'text-blue-500' : 'text-gray-400 hover:text-gray-300'
                                }`}
                        >
                            <Icon size={20} />
                            <span className="text-xs font-medium">{label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default MobileBottomNav;