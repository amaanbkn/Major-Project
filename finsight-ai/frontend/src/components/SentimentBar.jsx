import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';

export const SentimentBar = ({ score = 50 }) => {
  const [fillWidth, setFillWidth] = useState(0);

  useEffect(() => {
    // Animate on load
    const timer = setTimeout(() => {
      setFillWidth(score);
    }, 100);
    return () => clearTimeout(timer);
  }, [score]);

  // Interpolate color from Red (0) to Green (100)
  const isBullish = score >= 50;

  return (
    <Card className="p-5">
      <h3 className="text-sm font-semibold text-[#111111] mb-4">Market Sentiment</h3>
      
      <div className="relative h-2 bg-[#E5E7EB] rounded-full overflow-hidden">
        <div 
          className="absolute top-0 left-0 h-full transition-all duration-800 ease-out flex items-center justify-end"
          style={{ 
            width: `${fillWidth}%`, 
            background: `linear-gradient(90deg, #EF4444 0%, #22C55E 100%)` 
          }}
        >
        </div>
      </div>
      
      <div className="flex justify-between items-center mt-3 tracking-[0.08em] uppercase">
        <span className="text-[11px] font-semibold text-[#EF4444]">Bearish</span>
        <span className="text-[18px] font-bold tabular-nums text-[#111111]">{score}%</span>
        <span className="text-[11px] font-semibold text-[#22C55E]">Bullish</span>
      </div>
    </Card>
  );
};
