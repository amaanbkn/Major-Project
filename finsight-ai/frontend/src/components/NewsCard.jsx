import React from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';

export const NewsCard = ({ news = [] }) => {
  if (!news || news.length === 0) return null;

  return (
    <Card className="p-0 overflow-hidden">
      <div className="px-5 py-4 border-b border-[#E5E7EB]">
        <h3 className="text-sm font-semibold text-[#111111]">Latest News</h3>
      </div>
      <div className="flex flex-col">
        {news.map((item, index) => (
          <div
            key={item.id || index}
            className={`px-5 py-4 hover:bg-[#F7F8F5] transition-colors duration-150 cursor-pointer ${index !== news.length - 1 ? 'border-b border-[#E5E7EB]' : ''
              }`}
          >
            <div className="flex justify-between items-center mb-1.5">
              <Badge variant="neutral" className="text-[9px] px-1.5 py-0.5 rounded-[4px]">{item.source}</Badge>
              <span className="text-[11px] text-[#6B7280]">{item.time || item.published_at}</span>
            </div>
            <p className="text-[14px] font-medium text-[#111111] leading-snug line-clamp-2">
              {item.headline || item.title}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
};
