import React from 'react';
import { Settings as SettingsIcon, Shield, Bell, Database, User } from 'lucide-react';

const Settings = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">System Settings</h1>
                <p className="text-gray-400 text-sm">Configure IDS parameters and preferences</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Settings Nav */}
                <div className="col-span-1 space-y-2">
                    {[
                        { label: 'General', icon: SettingsIcon, active: true },
                        { label: 'Security Rules', icon: Shield, active: false },
                        { label: 'Notifications', icon: Bell, active: false },
                        { label: 'Database', icon: Database, active: false },
                        { label: 'Account', icon: User, active: false },
                    ].map((item) => (
                        <button
                            key={item.label}
                            className={`w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 transition-colors ${item.active
                                    ? 'bg-[#1E293B] text-blue-400 border border-blue-500/20'
                                    : 'text-gray-400 hover:bg-[#1E293B]/50 hover:text-gray-200'
                                }`}
                        >
                            <item.icon className="w-4 h-4" />
                            <span className="text-sm font-medium">{item.label}</span>
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="col-span-1 md:col-span-3 bg-[#1E293B] rounded-xl border border-gray-700 p-6">
                    <h2 className="text-lg font-bold text-white mb-6">General Configuration</h2>

                    <div className="space-y-6">
                        <div className="flex items-center justify-between py-4 border-b border-gray-700">
                            <div>
                                <h3 className="text-gray-200 font-medium">Dark Mode</h3>
                                <p className="text-gray-500 text-sm">Enable system-wide dark theme</p>
                            </div>
                            <div className="w-11 h-6 bg-blue-600 rounded-full relative cursor-pointer">
                                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow"></div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between py-4 border-b border-gray-700">
                            <div>
                                <h3 className="text-gray-200 font-medium">Auto-Refresh</h3>
                                <p className="text-gray-500 text-sm">Automatically refresh dashboard data</p>
                            </div>
                            <div className="w-11 h-6 bg-gray-700 rounded-full relative cursor-pointer">
                                <div className="absolute left-1 top-1 w-4 h-4 bg-gray-400 rounded-full shadow"></div>
                            </div>
                        </div>

                        <div className="py-2">
                            <label className="block text-gray-400 text-sm mb-2">System Name</label>
                            <input type="text" defaultValue="CyberWatch IDS-01" className="w-full max-w-md bg-[#0F172A] border border-gray-700 rounded-lg px-4 py-2 text-gray-200 text-sm" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
