import React, { useState } from 'react';
import { Bell, Search, Menu } from 'lucide-react';

const Header = () => {
    const [query, setQuery] = useState('');

    return (
        <header className="ids-header">
            {/* Left */}
            <div className="flex items-center gap-3">
                <div className="badge badge-online">
                    <span className="live-dot" style={{ width: 5, height: 5 }} />
                    System Online
                </div>
                <div className="divider-aurora" style={{ width: 1, height: 16, display: 'inline-block' }} />
                <span
                    className="mono text-[10px] hidden md:block"
                    style={{ color: 'var(--text-dim)' }}
                >
                    {new Date().toLocaleTimeString('en-US', { hour12: false })} · UTC+3
                </span>
            </div>

            {/* Right */}
            <div className="flex items-center gap-4">
                {/* Search */}
                <div className="relative hidden md:block">
                    <Search
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none"
                        style={{ color: 'var(--text-dim)' }}
                        strokeWidth={1.75}
                    />
                    <input
                        type="text"
                        className="ids-search"
                        placeholder="Search events, IPs…"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                    />
                </div>

                {/* Notifications */}
                <button
                    className="relative"
                    style={{ color: 'var(--text-dim)' }}
                    aria-label="Notifications"
                >
                    <Bell className="w-4 h-4" strokeWidth={1.75} />
                    <span
                        className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full flex items-center justify-center"
                        style={{ background: 'var(--neon-danger)', boxShadow: '0 0 6px var(--neon-danger)' }}
                    />
                </button>

                <div style={{ width: 1, height: 18, background: 'var(--border-subtle)' }} />

                {/* Avatar */}
                <div className="flex items-center gap-2.5 cursor-pointer group">
                    <div className="text-right hidden sm:block">
                        <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Admin</p>
                        <p className="text-[10px]" style={{ color: 'var(--text-dim)' }}>SecOps</p>
                    </div>
                    <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm text-white transition-all duration-200 group-hover:scale-105"
                        style={{
                            background: 'linear-gradient(135deg, var(--aurora-violet), var(--aurora-cyan))',
                            boxShadow: '0 0 12px rgba(124,58,237,0.4)',
                        }}
                    >
                        A
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
