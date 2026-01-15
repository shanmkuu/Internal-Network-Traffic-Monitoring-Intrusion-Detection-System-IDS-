import React, { useEffect, useState } from 'react';
import { Search, Filter, Download, Info, AlertTriangle, XCircle, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';
import { format } from 'date-fns';

const Logs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchLogs = async () => {
        const data = await api.getLogs();
        setLogs(data);
        setLoading(false);
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 5000);
        return () => clearInterval(interval);
    }, []);

    const filteredLogs = logs.filter(log =>
        log.source_ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.alert_type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const exportLogs = () => {
        const dataStr = JSON.stringify(logs, null, 2);
        const blob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = "system_logs.json";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">System Logs</h1>
                    <p className="text-gray-400 text-sm">Review and analyze system events</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={exportLogs}
                        className="px-4 py-2 bg-[#1E293B] text-gray-300 rounded-lg text-sm font-medium border border-gray-700 hover:bg-[#334155] flex items-center gap-2"
                    >
                        <Download className="w-4 h-4" /> Export
                    </button>
                </div>
            </div>

            <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-4">
                {/* Search & Filter Toolbar */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Search logs by Source, Type, or Message..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-[#0F172A] border border-gray-700 rounded-lg text-gray-200 text-sm focus:outline-none focus:border-blue-500"
                        />
                    </div>
                </div>

                {/* Log Table */}
                <div className="rounded-lg border border-gray-700 overflow-hidden">
                    <table className="w-full text-left text-sm text-gray-400">
                        <thead className="bg-[#0F172A] text-gray-200 font-medium border-b border-gray-700">
                            <tr>
                                <th className="px-4 py-3">Timestamp</th>
                                <th className="px-4 py-3">Level</th>
                                <th className="px-4 py-3">Source</th>
                                <th className="px-4 py-3">Type</th>
                                <th className="px-4 py-3">Message</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700 bg-[#1E293B]">
                            {loading ? (
                                <tr>
                                    <td colSpan="5" className="text-center py-4">Loading logs...</td>
                                </tr>
                            ) : filteredLogs.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="text-center py-4">No logs found</td>
                                </tr>
                            ) : (
                                filteredLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-[#334155]/50">
                                        <td className="px-4 py-3 font-mono text-gray-500">
                                            {format(new Date(log.created_at), 'yyyy-MM-dd HH:mm:ss')}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="text-blue-400 font-medium flex items-center gap-1">
                                                <Info className="w-3 h-3" /> INFO
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 font-mono">{log.source_ip === 'localhost' ? 'System' : log.source_ip}</td>
                                        <td className="px-4 py-3 text-white">{log.alert_type}</td>
                                        <td className="px-4 py-3">{log.description}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Logs;
