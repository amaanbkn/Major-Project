import React from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';

const mockIPOs = [
  {
    name: 'Bharti Hexacom Ltd',
    sector: 'Telecom',
    band: '₹542 - ₹570',
    gmp: '₹85',
    estListing: '₹655 (15%)',
    open: 'Apr 03, 2024',
    close: 'Apr 05, 2024',
    subscription: 75,
    status: 'ACTIVE'
  },
  {
    name: 'Teerth Gopicon Ltd',
    sector: 'Real Estate',
    band: '₹111',
    gmp: '₹22',
    estListing: '₹133 (20%)',
    open: 'Apr 08, 2024',
    close: 'Apr 10, 2024',
    subscription: 10,
    status: 'UPCOMING'
  },
  {
    name: 'Greenhitech Ventures',
    sector: 'Energy',
    band: '₹50 - ₹54',
    gmp: '₹10',
    estListing: '₹64 (18%)',
    open: 'Apr 12, 2024',
    close: 'Apr 15, 2024',
    subscription: 0,
    status: 'UPCOMING'
  },
  {
    name: 'Athaang Infrastructure',
    sector: 'Infrastructure',
    band: '₹120 - ₹128',
    gmp: '-₹5',
    estListing: '₹123 (-4%)',
    open: 'Mar 26, 2024',
    close: 'Mar 28, 2024',
    subscription: 100,
    status: 'CLOSED'
  }
];

export default function IPOTracker() {
  return (
    <div className="flex flex-col gap-6 pb-10">
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-2">
        <div>
          <h1 className="text-[28px] font-bold text-[#111111] leading-tight">IPO Tracker</h1>
          <p className="text-[#6B7280] text-sm mt-1">Upcoming & current IPOs with Grey Market Premium</p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm">Historical</Button>
          <Button variant="primary" size="sm">+ Set Alert</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {mockIPOs.map((ipo, idx) => (
          <Card key={idx} hoverable={true} className="p-6 flex flex-col h-full bg-white relative">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-bold text-[#111111] mb-1.5">{ipo.name}</h2>
                <Badge variant="neutral">{ipo.sector}</Badge>
              </div>
              <Badge variant={ipo.status === 'ACTIVE' ? 'success' : ipo.status === 'CLOSED' ? 'neutral' : 'dark'}>
                {ipo.status}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-y-5 gap-x-4 mb-6">
              <div>
                <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">Price Band</span>
                <span className="text-[15px] font-bold tabular-nums text-[#111111]">{ipo.band}</span>
              </div>
              <div>
                <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">GMP</span>
                <span className={`text-[15px] font-bold tabular-nums ${ipo.gmp.includes('-') ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                  {ipo.gmp} <span className="text-xs font-semibold">({ipo.estListing})</span>
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">Open Date</span>
                <span className="text-[13px] font-medium text-[#111111]">{ipo.open}</span>
              </div>
              <div>
                <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">Close Date</span>
                <span className="text-[13px] font-medium text-[#111111]">{ipo.close}</span>
              </div>
            </div>

            <div className="mt-auto pt-4 border-t border-[#E5E7EB]">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold text-[#111111]">Subscription Level</span>
                <span className="text-xs font-medium text-[#6B7280]">{ipo.subscription}%</span>
              </div>
              <div className="w-full h-1.5 bg-[#F3F4F6] rounded-full overflow-hidden mb-5">
                <div 
                  className={`h-full ${ipo.subscription >= 100 ? 'bg-[#22C55E]' : ipo.subscription > 0 ? 'bg-[#111111]' : 'bg-transparent'}`} 
                  style={{ width: `${Math.min(ipo.subscription, 100)}%` }}
                ></div>
              </div>
              
              <Button variant="primary" className="w-full">
                Analyse with AI
              </Button>
            </div>
          </Card>
        ))}
      </div>

    </div>
  );
}
