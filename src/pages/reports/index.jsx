import React from 'react';
import { FileText, Calendar, Download, ChevronDown } from 'lucide-react';

const Reports = () => {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">Reports Generating</h1>
                    <p className="text-gray-400 text-sm">Generate and export system security reports</p>
                </div>
                <div className="flex gap-3">
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 shadow-lg shadow-blue-500/20 flex items-center gap-2">
                        <Download className="w-4 h-4" /> Generate Report
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Configuration Card */}
                <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-6">
                    <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-blue-500" /> Report Configuration
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-gray-400 text-sm mb-2">Date Range</label>
                            <div className="grid grid-cols-2 gap-4">
                                <input type="date" className="bg-[#0F172A] border border-gray-700 rounded-lg px-4 py-2 text-gray-200 text-sm w-full" />
                                <input type="date" className="bg-[#0F172A] border border-gray-700 rounded-lg px-4 py-2 text-gray-200 text-sm w-full" />
                            </div>
                        </div>

                        <div>
                            <label className="block text-gray-400 text-sm mb-2">Report Type</label>
                            <div className="relative">
                                <select className="bg-[#0F172A] border border-gray-700 rounded-lg px-4 py-2 text-gray-200 text-sm w-full appearance-none">
                                    <option>Security Summary</option>
                                    <option>Traffic Analysis</option>
                                    <option>Incident Detail</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Preview Card */}
                <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-6 flex flex-col items-center justify-center text-center opacity-75">
                    <FileText className="w-16 h-16 text-gray-600 mb-4" />
                    <h4 className="text-gray-300 font-medium">Report Preview</h4>
                    <p className="text-gray-500 text-sm mt-2 max-w-xs">Select parameters and click generate to view a preview of your report here.</p>
                </div>
            </div>
        </div>
    );
};

export default Reports;
