import React, { createContext, useContext, useState } from 'react';

const TabsContext = createContext({});

export const Tabs = ({ defaultValue, className, children }) => {
    const [activeTab, setActiveTab] = useState(defaultValue);

    return (
        <TabsContext.Provider value={{ activeTab, setActiveTab }}>
            <div className={`w-full ${className || ''}`}>
                {children}
            </div>
        </TabsContext.Provider>
    );
};

export const TabsList = ({ className, children }) => {
    return (
        <div className={`inline-flex h-10 items-center justify-center rounded-lg bg-[#1A2332] p-1 text-gray-500 border border-white/5 ${className || ''}`}>
            {children}
        </div>
    );
};

export const TabsTrigger = ({ value, className, children }) => {
    const { activeTab, setActiveTab } = useContext(TabsContext);
    const isActive = activeTab === value;

    return (
        <button
            onClick={() => setActiveTab(value)}
            className={`
                inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50
                ${isActive
                    ? 'bg-[#2D3B4E] text-white shadow-sm'
                    : 'hover:bg-white/5 hover:text-gray-300'
                }
                ${className || ''}
            `}
        >
            {children}
        </button>
    );
};

export const TabsContent = ({ value, className, children }) => {
    const { activeTab } = useContext(TabsContext);

    if (activeTab !== value) return null;

    return (
        <div className={`mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 animated-fade-in ${className || ''}`}>
            {children}
        </div>
    );
};
