import React from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';

const mockNews = [
  { id: 1, source: "ET", headline: "Reliance Industries reports 15% surge in quarterly profit, beats estimates", time: "2h ago" },
  { id: 2, source: "MC", headline: "Nifty crosses 22,500 mark for the first time, financials lead the rally", time: "4h ago" },
  { id: 3, source: "Reddit", headline: "Why Tata Motors is looking like a solid buy right now (DD inside)", time: "6h ago" },
  { id: 4, source: "ET", headline: "RBI keeps repo rate unchanged at 6.5%, maintains 'withdrawal of accommodation' stance", time: "8h ago" },
];

export const NewsCard = () => {
  return (
    <Card className="p-0 overflow-hidden">
      <div className="px-5 py-4 border-b border-[#E5E7EB]">
        <h3 className="text-sm font-semibold text-[#111111]">Latest News</h3>
      </div>
      <div className="flex flex-col">
        {mockNews.map((item, index) => (
          <div
            key={item.id}
            className={`px-5 py-4 hover:bg-[#F7F8F5] transition-colors duration-150 cursor-pointer ${index !== mockNews.length - 1 ? 'border-b border-[#E5E7EB]' : ''
              }`}
          >
            <div className="flex justify-between items-center mb-1.5">
              <Badge variant="neutral" className="text-[9px] px-1.5 py-0.5 rounded-[4px]">{item.source}</Badge>
              <span className="text-[11px] text-[#6B7280]">{item.time}</span>
            </div>
            <p className="text-[14px] font-medium text-[#111111] leading-snug line-clamp-2">
              {item.headline}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
};
