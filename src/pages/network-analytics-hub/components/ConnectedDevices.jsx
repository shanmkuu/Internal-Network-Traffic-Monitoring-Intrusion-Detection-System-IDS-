import React, { useState, useEffect } from 'react';
import AppIcon from '../../../components/AppIcon';

const ConnectedDevices = () => {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchDevices = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/devices');
            const data = await response.json();
            setDevices(data || []);
        } catch (error) {
            console.error("Failed to fetch devices:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDevices();
        const interval = setInterval(fetchDevices, 10000);
        return () => clearInterval(interval);
    }, []);

    const getRiskColor = (level) => {
        switch (level?.toLowerCase()) {
            case 'high': return 'bg-red-500/10 text-red-400 border-red-500/20';
            case 'medium': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
            default: return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
        }
    };

    const getDeviceIcon = (type) => {
        if (!type) return "Laptop";
        const t = type.toLowerCase();
        if (t.includes("phone") || t.includes("mobile")) return "Smartphone";
        if (t.includes("router") || t.includes("gateway")) return "Router";
        if (t.includes("printer")) return "Printer";
        if (t.includes("server")) return "Server";
        return "Laptop";
    };

    return (
        <div className="bg-[#1A1F2B]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-2xl h-full flex flex-col">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
                        <AppIcon name="Server" className="w-5 h-5 text-indigo-400" />
                        Network Inventory
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">Discovered devices & risk analysis</p>
                </div>
                <div className="bg-indigo-500/10 px-3 py-1.5 rounded-lg border border-indigo-500/20">
                    <span className="text-indigo-400 font-mono text-sm">{devices.length} Devices</span>
                </div>
            </div>

            <div className="overflow-x-auto custom-scrollbar flex-1">
                <table className="w-full text-left border-collapse">
                    <thead className="text-xs uppercase bg-white/5 text-gray-400 font-semibold sticky top-0 backdrop-blur-md z-10">
                        <tr>
                            <th className="px-4 py-3 rounded-l-lg">Type</th>
                            <th className="px-4 py-3">Device / Name</th>
                            <th className="px-4 py-3">IP Address</th>
                            <th className="px-4 py-3">MAC Address</th>
                            <th className="px-4 py-3">Vendor / OS</th>
                            <th className="px-4 py-3 rounded-r-lg">Risk & Services</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-sm">
                        {loading && devices.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="text-center py-8 text-gray-500 animate-pulse">
                                    Scanning network...
                                </td>
                            </tr>
                        ) : devices.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="text-center py-8 text-gray-500">
                                    No devices discovered.
                                </td>
                            </tr>
                        ) : (
                            devices.map((device, index) => (
                                <tr key={index} className="hover:bg-white/5 transition-colors group">
                                    <td className="px-4 py-3">
                                        <div className="p-2 bg-indigo-500/10 rounded-lg w-fit text-indigo-400 group-hover:scale-110 transition-transform">
                                            <AppIcon name={getDeviceIcon(device.device_type)} className="w-4 h-4" />
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="font-medium text-white">
                                            {device.hostname || device.custom_name || "Unknown Host"}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                                        {device.ip_address || device.ip || "N/A"}
                                    </td>
                                    <td className="px-4 py-3 text-gray-400 font-mono text-xs">
                                        {device.mac_address || device.mac || "N/A"}
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col">
                                            <span className="text-gray-300">{device.vendor || "Unknown"}</span>
                                            {device.os_family && (
                                                <span className="text-[10px] text-gray-500 flex items-center gap-1">
                                                    <AppIcon name="Cpu" className="w-3 h-3" />
                                                    {device.os_family}
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col gap-1 items-start">
                                            <span className={`text-[10px] px-2 py-0.5 rounded border uppercase font-bold tracking-wider ${getRiskColor(device.risk_level)}`}>
                                                {device.risk_level || "LOW"}
                                            </span>
                                            {/* Protocols / Ports */}
                                            {device.protocols_detected && device.protocols_detected.length > 0 ? (
                                                <div className="flex flex-wrap gap-1 max-w-[120px]">
                                                    {device.protocols_detected.slice(0, 3).map((p, i) => (
                                                        <span key={i} className="text-[9px] text-gray-500 bg-white/5 px-1 rounded">{p}</span>
                                                    ))}
                                                </div>
                                            ) : (
                                                (device.open_ports && device.open_ports.length > 0) && (
                                                    <span className="text-[9px] text-gray-600">
                                                        Ports: {Array.isArray(device.open_ports) ? device.open_ports.length : 1}
                                                    </span>
                                                )
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ConnectedDevices;
