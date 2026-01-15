import React, { useEffect, useState } from 'react';
import { Zap, Monitor } from 'lucide-react';
import { api } from '../../../services/api';

const TopTalkersList = () => {
  const [talkers, setTalkers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTalkers = async () => {
      const data = await api.getTopSources();
      setTalkers(data);
      setLoading(false);
    };

    fetchTalkers();
    const interval = setInterval(fetchTalkers, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-gray-500 text-center">Loading top sources...</div>;

  return (
    <div className="bg-[#1A2332] p-8 rounded-2xl border border-white/5 h-80 flex flex-col">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 backdrop-blur-sm shadow-inner shadow-amber-500/10">
          <Zap className="w-5 h-5 text-amber-500" />
        </div>
        <h3 className="text-white font-bold">Top Threat Sources</h3>
      </div>

      {talkers.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <Zap className="w-16 h-16 text-amber-500/20 mb-4" />
          <p className="text-gray-500 text-sm">No threat sources detected yet</p>
        </div>
      ) : (
        <div className="overflow-y-auto flex-1 pr-2">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-gray-500 border-b border-gray-700/50">
              <tr>
                <th className="pb-2">Source IP</th>
                <th className="pb-2 text-right">Events</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/30">
              {talkers.map((item, index) => (
                <tr key={item.ip} className="group hover:bg-white/5 transition-colors">
                  <td className="py-2 text-gray-300 font-mono flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${index === 0 ? 'bg-red-500' : 'bg-gray-500'}`}></div>
                    {item.ip}
                  </td>
                  <td className="py-2 text-right font-bold text-white">
                    {item.count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TopTalkersList;
