import React, { useState, useEffect } from 'react';
import { api } from '../../../services/api';
import { Wifi, Router, Laptop, Smartphone, HelpCircle, RefreshCw } from 'lucide-react';

const DeviceIcon = ({ vendor }) => {
    // Simple logic to guess icon based on vendor or MAC, 
    // real implementation would be more robust.
    const v = (vendor || "").toLowerCase();
    if (v.includes("apple") || v.includes("samsung")) return <Smartphone className="w-4 h-4 text-purple-400" />;
    if (v.includes("intel") || v.includes("dell")) return <Laptop className="w-4 h-4 text-blue-400" />;
    if (v.includes("cisco") || v.includes("gateway")) return <Router className="w-4 h-4 text-orange-400" />;
    return <Wifi className="w-4 h-4 text-gray-400" />;
};

const ConnectedDevices = () => {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchDevices = async () => {
        const data = await api.getDevices();
        setDevices(data || []);
        setLoading(false);
    };

    useEffect(() => {
        fetchDevices();
        const interval = setInterval(fetchDevices, 5000); // Poll local cache every 5s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-white font-bold flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 backdrop-blur-sm shadow-inner shadow-emerald-500/10">
                        <Wifi className="w-5 h-5 text-emerald-500" />
                    </div>
                    Connected Devices
                </h3>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 bg-[#0F172A] px-2 py-1 rounded">
                        Scanning Subnet (Active)
                    </span>
                    <button onClick={() => { setLoading(true); fetchDevices(); }} className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-gray-400">
                    <thead className="text-xs uppercase bg-[#0F172A] text-gray-500">
                        <tr>
                            <th className="px-4 py-3 rounded-l-lg">Type</th>
                            <th className="px-4 py-3">IP Address</th>
                            <th className="px-4 py-3">MAC Address</th>
                            <th className="px-4 py-3">Vendor</th>
                            <th className="px-4 py-3 rounded-r-lg">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {loading && devices.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="text-center py-4">Scanning network...</td>
                            </tr>
                        ) : devices.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="text-center py-4">No devices found</td>
                            </tr>
                        ) : (
                            devices.map((device, index) => (
                                <tr key={`${device.ip}-${index}`} className="hover:bg-[#0F172A]/50 transition-colors">
                                    <td className="px-4 py-3">
                                        <div className="p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm w-fit shadow-sm">
                                            <DeviceIcon vendor={device.vendor} />
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-white font-mono">{device.ip}</td>
                                    <td className="px-4 py-3 font-mono text-gray-500">{device.mac}</td>
                                    <td className="px-4 py-3">{device.vendor}</td>
                                    <td className="px-4 py-3">
                                        <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full w-fit">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                            {device.status}
                                        </span>
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
