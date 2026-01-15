import React from 'react';
import { Network, Globe, Lock, Server, Activity, Radio, Pause, Square, Play } from 'lucide-react';

const ProtocolFilters = () => {
    const protocols = [
        { id: 'tcp', label: 'TCP', icon: Network, color: 'bg-blue-600' },
        { id: 'udp', label: 'UDP', icon: Radio, color: 'bg-purple-600' },
        { id: 'http', label: 'HTTP', icon: Globe, color: 'bg-green-600' },
        { id: 'https', label: 'HTTPS', icon: Lock, color: 'bg-emerald-600' },
        { id: 'dns', label: 'DNS', icon: Server, color: 'bg-[#1A2332] hover:bg-[#243447]' }, // Darker/Inactive look from image
        { id: 'icmp', label: 'ICMP', icon: Activity, color: 'bg-[#1A2332] hover:bg-[#243447]' },
    ];

    return (
        <div className="bg-[#1A2332] rounded-2xl p-6 border border-white/5 h-full">
            <div className="grid grid-cols-3 gap-4 mb-4">
                {protocols.map((p) => (
                    <button
                        key={p.id}
                        className={`${p.color} h-24 rounded-xl flex flex-col items-center justify-center gap-2 transition-transform hover:scale-105 active:scale-95 shadow-lg group`}
                    >
                        <p.icon className="w-6 h-6 text-white" />
                        <span className="text-white font-bold tracking-wide text-sm">{p.label}</span>
                    </button>
                ))}
            </div>

            {/* Control Actions Row (Pause, Stop, Status) - Matching the right side of the image block visually */}
            {/* Note: In the image, these are separate. I will place them next to the protocols or in the main grid. 
          Actually, the image has Protocol block separate from Control block. 
          Let's separate them in the parent index.jsx. 
      */}
        </div>
    );
};

export default ProtocolFilters;
