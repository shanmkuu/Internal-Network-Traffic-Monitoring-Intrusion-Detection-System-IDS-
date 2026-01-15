import React from 'react';
import { Bell, Search, User } from 'lucide-react';

const Header = () => {
    return (
        <header className="h-16 bg-[#0F172A] border-b border-gray-800 flex items-center justify-between px-8 sticky top-0 z-20 w-full">
            {/* Left: System Awareness */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span className="text-xs font-medium text-emerald-500 uppercase tracking-wider">System Active</span>
                </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-6">
                {/* Search */}
                <div className="relative hidden md:block w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Global Search..."
                        className="w-full pl-10 pr-4 py-1.5 bg-[#1E293B] border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500 placeholder-gray-500 transition-colors"
                    />
                </div>

                <div className="h-6 w-px bg-gray-800"></div>

                {/* Icons */}
                <div className="flex items-center gap-4">
                    <button className="relative text-gray-400 hover:text-white transition-colors">
                        <Bell className="w-5 h-5" />
                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                    </button>

                    <button className="flex items-center gap-3 pl-4 border-l border-gray-800">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-white">Admin User</p>
                            <p className="text-xs text-gray-400">Security Ops</p>
                        </div>
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold border border-blue-500 shadow-lg shadow-blue-500/20">
                            <User className="w-4 h-4" />
                        </div>
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Header;
