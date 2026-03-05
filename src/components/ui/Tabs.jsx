import React, { createContext, useContext, useState } from 'react';

const TabsContext = createContext({});

export const Tabs = ({ defaultValue, className, children }) => {
    const [activeTab, setActiveTab] = useState(defaultValue);
    return (
        <TabsContext.Provider value={{ activeTab, setActiveTab }}>
            <div className={`w-full ${className || ''}`}>{children}</div>
        </TabsContext.Provider>
    );
};

export const TabsList = ({ className, children }) => (
    <div
        className={`inline-flex items-center gap-1 p-1 rounded-lg ${className || ''}`}
        style={{
            background: 'var(--bg-panel)',
            border: '1px solid var(--border-subtle)',
        }}
    >
        {children}
    </div>
);

export const TabsTrigger = ({ value, className, children }) => {
    const { activeTab, setActiveTab } = useContext(TabsContext);
    const isActive = activeTab === value;

    return (
        <button
            onClick={() => setActiveTab(value)}
            className={`relative px-4 py-1.5 rounded-md text-xs font-semibold transition-all duration-200 ${className || ''}`}
            style={{
                color: isActive ? 'var(--neon-primary)' : 'var(--text-dim)',
                background: isActive ? 'rgba(124,58,237,0.15)' : 'transparent',
                border: isActive ? '1px solid rgba(124,58,237,0.25)' : '1px solid transparent',
                boxShadow: isActive ? '0 0 12px rgba(124,58,237,0.15)' : 'none',
                letterSpacing: '0.03em',
            }}
        >
            {children}
        </button>
    );
};

export const TabsContent = ({ value, className, children }) => {
    const { activeTab } = useContext(TabsContext);
    if (activeTab !== value) return null;
    return (
        <div
            className={`mt-4 animate-float-up ${className || ''}`}
            style={{ animationDuration: '0.3s' }}
        >
            {children}
        </div>
    );
};
