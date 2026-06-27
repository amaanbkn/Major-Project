import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Loader2 } from 'lucide-react';
import { getIPOs, getGMPData, analyzeIPO } from '../api';

export default function IPOTracker() {
  const [ipos, setIpos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analyzingName, setAnalyzingName] = useState(null);
  const [analysisText, setAnalysisText] = useState('');
  const [selectedIpo, setSelectedIpo] = useState(null);

  const handleAnalyze = async (ipo) => {
    setAnalyzingName(ipo.name);
    setAnalysisText('');
    try {
      const res = await analyzeIPO({
        name: ipo.name,
        band: ipo.price_band || ipo.band || 'TBA',
        gmp: ipo.gmp || 'N/A',
        estListing: ipo.estListing || 'N/A',
        open: ipo.open_date || ipo.open || 'TBA',
        close: ipo.close_date || ipo.close || 'TBA',
        subscription: parseFloat(ipo.subscription) || 0.0,
        sector: ipo.sector || 'Various'
      });
      if (res && res.analysis) {
        setAnalysisText(res.analysis);
      } else {
        setAnalysisText("Could not generate analysis.");
      }
      setSelectedIpo(ipo);
    } catch (err) {
      setAnalysisText(err.message || "Failed to analyze IPO.");
      setSelectedIpo(ipo);
    } finally {
      setAnalyzingName(null);
    }
  };

  useEffect(() => {
    async function fetchIPOData() {
      try {
        setLoading(true);
        // Fetch base IPO details and GMP data in parallel
        const [ipoRes, gmpRes] = await Promise.allSettled([
          getIPOs(),
          getGMPData()
        ]);

        let mergedIpos = [];
        
        // Check if getIPOs succeeded
        if (ipoRes.status === 'fulfilled' && ipoRes.value && ipoRes.value.ipos) {
          mergedIpos = ipoRes.value.ipos;
        }

        // Merge GMP data if available
        if (gmpRes.status === 'fulfilled' && gmpRes.value && gmpRes.value.gmp_data) {
          const gmpMap = {};
          gmpRes.value.gmp_data.forEach(item => {
            gmpMap[item.symbol || item.name] = item;
          });
          
          mergedIpos = mergedIpos.map(ipo => {
            const gmpInfo = gmpMap[ipo.symbol] || gmpMap[ipo.name];
            if (gmpInfo) {
              return {
                ...ipo,
                gmp: gmpInfo.gmp || ipo.gmp,
                estListing: gmpInfo.estListing || ipo.estListing,
                subscription: gmpInfo.subscription || ipo.subscription
              };
            }
            return ipo;
          });
        }

        setIpos(mergedIpos);
      } catch (err) {
        setError("Failed to load IPO data");
      } finally {
        setLoading(false);
      }
    }
    
    fetchIPOData();
  }, []);

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

      {error && (
        <div className="bg-red-50 text-red-500 p-4 rounded-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="w-10 h-10 animate-spin text-[#E5E7EB]" />
        </div>
      ) : ipos.length === 0 ? (
        <Card className="p-8 text-center text-[#6B7280]">
          No active or upcoming IPOs found at the moment.
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {ipos.map((ipo, idx) => {
            const isNegativeGMP = String(ipo.gmp || '').includes('-');
            const status = ipo.status || 'UPCOMING';
            const subLvl = ipo.subscription || 0;
            
            return (
              <Card key={idx} hoverable={true} className="p-6 flex flex-col h-full bg-white relative">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-[#111111] mb-1.5">{ipo.name}</h2>
                    <Badge variant="neutral">{ipo.sector || 'Various'}</Badge>
                  </div>
                  <Badge variant={status === 'ACTIVE' ? 'success' : status === 'CLOSED' ? 'neutral' : 'dark'}>
                    {status}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-y-5 gap-x-4 mb-6">
                  <div>
                    <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">Price Band</span>
                    <span className="text-[15px] font-bold tabular-nums text-[#111111]">{ipo.band || 'TBA'}</span>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">GMP</span>
                    <span className={`text-[15px] font-bold tabular-nums ${isNegativeGMP ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                      {ipo.gmp || 'N/A'} <span className="text-xs font-semibold">({ipo.estListing || 'N/A'})</span>
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">Open Date</span>
                    <span className="text-[13px] font-medium text-[#111111]">{ipo.open || 'TBA'}</span>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] block mb-1">Close Date</span>
                    <span className="text-[13px] font-medium text-[#111111]">{ipo.close || 'TBA'}</span>
                  </div>
                </div>

                <div className="mt-auto pt-4 border-t border-[#E5E7EB]">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-[#111111]">Subscription Level</span>
                    <span className="text-xs font-medium text-[#6B7280]">{subLvl}x</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#F3F4F6] rounded-full overflow-hidden mb-5">
                    <div 
                      className={`h-full ${subLvl >= 1 ? 'bg-[#22C55E]' : subLvl > 0 ? 'bg-[#111111]' : 'bg-transparent'}`} 
                      style={{ width: `${Math.min((subLvl / Math.max(1, subLvl)) * 100, 100)}%` }}
                    ></div>
                  </div>
                  
                  <Button 
                    variant="primary" 
                    className="w-full flex items-center justify-center gap-1.5"
                    disabled={analyzingName !== null}
                    onClick={() => handleAnalyze(ipo)}
                  >
                    {analyzingName === ipo.name ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      'Analyse with AI'
                    )}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* AI Analysis Modal */}
      {selectedIpo && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <Card className="w-full max-w-[650px] max-h-[85vh] flex flex-col p-0 overflow-hidden shadow-2xl border-none animate-in slide-in-from-bottom-4 duration-300">
            {/* Modal Header */}
            <div className="px-6 py-5 border-b border-[#E5E7EB] bg-white flex justify-between items-center shrink-0">
              <div>
                <h3 className="text-lg font-bold text-[#111111]">AI In-depth Analysis</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Evaluating IPO for {selectedIpo.name}</p>
              </div>
              <button 
                onClick={() => { setSelectedIpo(null); setAnalysisText(''); }}
                className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-[#F3F4F6] text-[#6B7280] transition-colors cursor-pointer text-sm font-semibold"
              >
                ✕
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="flex-1 p-6 overflow-y-auto bg-[#F7F8F5] text-sm leading-relaxed text-[#111111] border-b border-[#E5E7EB]">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap font-sans text-gray-800">
                {analysisText}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-white flex justify-end shrink-0">
              <Button variant="primary" onClick={() => { setSelectedIpo(null); setAnalysisText(''); }}>
                Close Analysis
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
