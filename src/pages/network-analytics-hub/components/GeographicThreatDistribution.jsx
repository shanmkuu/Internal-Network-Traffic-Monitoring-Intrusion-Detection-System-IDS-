import React, { useEffect, useState } from 'react';
import { Globe, MapPin } from 'lucide-react';
import { api } from '../../../services/api';

const GeographicThreatDistribution = () => {
  const [geoData, setGeoData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGeo = async () => {
      const data = await api.getGeoDistribution();
      setGeoData(data);
      setLoading(false);
    };

    fetchGeo();
    const interval = setInterval(fetchGeo, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-gray-500 text-center">Loading map data...</div>;

  const total = geoData.reduce((acc, curr) => acc + curr.count, 0);

  return (
    <div className="bg-[#1A2332] p-8 rounded-2xl border border-white/5 h-80 flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Globe className="w-5 h-5 text-blue-500" />
        <h3 className="text-white font-bold">Geographic Distribution</h3>
      </div>

      {geoData.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <Globe className="w-16 h-16 text-blue-500/20 mb-4" />
          <p className="text-gray-500 text-sm">No geographic threat data available</p>
        </div>
      ) : (
        <div className="overflow-y-auto flex-1 pr-2 space-y-3">
          {geoData.map((item, index) => (
            <div key={item.country} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-300 flex items-center gap-2">
                  <MapPin className="w-3 h-3 text-gray-500" />
                  {item.country}
                </span>
                <span className="text-gray-400 font-mono">{((item.count / total) * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-gray-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-500"
                  style={{ width: `${(item.count / total) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GeographicThreatDistribution;
