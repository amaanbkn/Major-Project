import React from 'react';
import { Card } from './ui/Card';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const StockCard = ({ symbol, name, price, change, isPositive, chartData }) => {
  if (!symbol) return null;
  
  const defaultChartData = chartData || [
    { val: price * 0.98 }, { val: price * 0.99 }, { val: price * 0.97 }, { val: price }
  ];

  return (
    <Card className="p-5 flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-lg font-bold text-[#111111]">{symbol}</h2>
          <p className="text-xs text-[#6B7280]">{name || symbol}</p>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-[13px] font-medium ${
          isPositive ? 'bg-[#22C55E]/10 text-[#22C55E]' : 'bg-[#EF4444]/10 text-[#EF4444]'
        }`}>
          {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
          <span>{Math.abs(change).toFixed(2)}%</span>
        </div>
      </div>
      
      <div className="flex justify-between items-end">
        <span className="text-[32px] font-bold tabular-nums tracking-[-0.02em] leading-none text-[#111111]">
          ₹{price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
        
        <div className="h-[40px] w-[100px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={defaultChartData}>
              <Line 
                type="monotone" 
                dataKey="val" 
                stroke={isPositive ? "#22C55E" : "#EF4444"} 
                strokeWidth={2} 
                dot={false}
                isAnimationActive={true}
                animationDuration={1500}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  );
};
