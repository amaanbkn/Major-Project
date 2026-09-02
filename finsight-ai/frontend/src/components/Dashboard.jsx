import React, { useState, useEffect, useMemo } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import {
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useCountUp } from '../hooks/useCountUp';
import {
  getNifty50,
  getMarketSentiment,
  getNiftyHistory,
} from '../api';


/* ============================================================
   STAT CARD
   ============================================================ */

const StatCard = ({
  label,
  value,
  change,
  isPositive,
  suffix = '',
  prefix = '',
  loading = false,
}) => {
  const animatedValue = useCountUp(
    typeof value === 'number' && !loading ? value : 0
  );

  const displayValue = loading ? (
    <Loader2 className="w-6 h-6 animate-spin text-[#E5E7EB]" />
  ) : typeof value === 'number' ? (
    `${prefix}${animatedValue.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    })}${suffix}`
  ) : (
    value
  );

  return (
    <Card className="px-5 py-5 border-[#E5E7EB]">
      <div className="flex flex-col gap-1.5 cursor-default">
        <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">
          {label}
        </span>

        <div className="flex items-end justify-between mt-1 gap-3">
          <span className="text-[28px] font-bold tabular-nums text-[#111111] leading-none">
            {displayValue}
          </span>

          {change !== undefined && !loading && (
            <div
              className={`flex items-center gap-0.5 px-2 py-1 rounded-[6px] ${isPositive
                ? 'bg-[#22C55E]/10 text-[#22C55E]'
                : 'bg-[#EF4444]/10 text-[#EF4444]'
                }`}
            >
              {isPositive ? (
                <ArrowUpRight className="w-3.5 h-3.5" />
              ) : (
                <ArrowDownRight className="w-3.5 h-3.5" />
              )}

              <span className="text-[13px] font-semibold">
                {Math.abs(Number(change) || 0).toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};


/* ============================================================
   TOOLTIP
   ============================================================ */

const CustomTooltip = ({ active, payload, label }) => {
  if (
    active &&
    payload &&
    payload.length &&
    typeof payload[0]?.value === 'number'
  ) {
    return (
      <div className="bg-[#111111] text-white px-3 py-2 rounded-[8px] shadow-lg text-sm tabular-nums flex flex-col gap-1">
        <span className="text-[#9CA3AF] text-xs">
          {label}
        </span>

        <span className="font-semibold">
          ₹
          {payload[0].value.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </span>
      </div>
    );
  }

  return null;
};


/* ============================================================
   SENTIMENT LABEL
   ============================================================ */

function getSentimentLabel(score) {
  const numericScore = Number(score);

  if (!Number.isFinite(numericScore)) {
    return 'Neutral';
  }

  if (numericScore <= -0.15) {
    return 'Bearish';
  }

  if (numericScore < -0.05) {
    return 'Slightly Bearish';
  }

  if (numericScore <= 0.05) {
    return 'Neutral';
  }

  if (numericScore < 0.15) {
    return 'Slightly Bullish';
  }

  return 'Bullish';
}


/* ============================================================
   CHART DATA NORMALIZATION
   ============================================================ */

function normalizeHistory(history) {
  if (!Array.isArray(history)) {
    return [];
  }

  return history
    .map((item, index) => {
      const numericValue = Number(item?.value);

      if (!Number.isFinite(numericValue)) {
        return null;
      }

      return {
        time:
          item?.time ||
          item?.date ||
          `${index + 1}`,
        value: numericValue,
      };
    })
    .filter(Boolean);
}


/* ============================================================
   DASHBOARD
   ============================================================ */

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('1D');

  const ranges = [
    '1D',
    '7D',
    '1M',
    '1Y',
    'ALL',
  ];

  const [loading, setLoading] = useState(true);

  const [indexData, setIndexData] = useState({
    value: null,
    previous_close: null,
    change: null,
    change_pct: null,
  });

  const [stocks, setStocks] = useState([]);

  const [sentiment, setSentiment] = useState({
    overall_label: 'NEUTRAL',
    overall_score: 0,
  });

  const [chartData, setChartData] = useState([]);

  const [chartLoading, setChartLoading] = useState(false);

  const [chartError, setChartError] = useState('');


  /* ==========================================================
     FETCH DASHBOARD DATA
     ========================================================== */

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);

      try {
        const [
          niftyResult,
          sentimentResult,
        ] = await Promise.allSettled([
          getNifty50(),
          getMarketSentiment(),
        ]);

        if (cancelled) {
          return;
        }

        /* ------------------------------------------------------
           NIFTY
           ------------------------------------------------------ */

        if (
          niftyResult.status === 'fulfilled' &&
          niftyResult.value
        ) {
          const response = niftyResult.value;

          if (response.index) {
            setIndexData({
              value: response.index.value ?? null,
              previous_close:
                response.index.previous_close ?? null,
              change:
                response.index.change ?? null,
              change_pct:
                response.index.change_pct ?? null,
            });
          }

          if (Array.isArray(response.stocks)) {
            setStocks(response.stocks);
          } else {
            setStocks([]);
          }
        } else {
          setIndexData({
            value: null,
            previous_close: null,
            change: null,
            change_pct: null,
          });

          setStocks([]);
        }

        /* ------------------------------------------------------
           SENTIMENT
           ------------------------------------------------------ */

        if (
          sentimentResult.status === 'fulfilled' &&
          sentimentResult.value
        ) {
          setSentiment({
            ...sentimentResult.value,
            overall_score:
              Number(
                sentimentResult.value.overall_score
              ) || 0,
          });
        } else {
          setSentiment({
            overall_label: 'NEUTRAL',
            overall_score: 0,
          });
        }
      } catch (error) {
        console.error(
          'Dashboard data fetch failed:',
          error
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, []);


  /* ==========================================================
     FETCH CHART HISTORY
     ========================================================== */

  useEffect(() => {
    let cancelled = false;

    async function fetchHistory() {
      setChartLoading(true);
      setChartError('');

      try {
        const apiPeriod = timeRange.toLowerCase();

        const history = await getNiftyHistory(
          apiPeriod
        );

        const normalized = normalizeHistory(
          history
        );

        if (cancelled) {
          return;
        }

        if (normalized.length === 0) {
          setChartData([]);
          setChartError(
            'Historical NIFTY data is currently unavailable.'
          );
        } else {
          setChartData(normalized);
        }
      } catch (error) {
        console.error(
          'Failed to fetch NIFTY history:',
          error
        );

        if (!cancelled) {
          setChartData([]);
          setChartError(
            'Unable to load NIFTY historical data.'
          );
        }
      } finally {
        if (!cancelled) {
          setChartLoading(false);
        }
      }
    }

    fetchHistory();

    return () => {
      cancelled = true;
    };
  }, [timeRange]);


  /* ==========================================================
     DERIVED DATA
     ========================================================== */

  const topMovers = useMemo(() => {
    return [...stocks]
      .filter(
        (stock) =>
          stock &&
          Number.isFinite(Number(stock.change_pct))
      )
      .sort(
        (a, b) =>
          Math.abs(Number(b.change_pct) || 0) -
          Math.abs(Number(a.change_pct) || 0)
      )
      .slice(0, 5);
  }, [stocks]);


  const isMarketUp =
    Number(indexData.change_pct) >= 0;


  const sentimentScore =
    Number(sentiment.overall_score);

  const normalizedSentimentScore =
    Number.isFinite(sentimentScore)
      ? sentimentScore
      : 0;


  /*
   * IMPORTANT:
   * Calculate the displayed sentiment label from the same
   * overall_score used by the sentiment system.
   *
   * This prevents:
   * "Slightly Bullish" + bearish percentage
   * inconsistencies caused by separate frontend labels.
   */
  const displayedSentiment =
    getSentimentLabel(
      normalizedSentimentScore
    );


  const activeStocks = stocks.length;


  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <div className="flex flex-col gap-5 pb-10">

      {/* ========================================================
          TOP STATS
          ======================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">

        <StatCard
          label="NIFTY 50"
          value={indexData.value}
          change={indexData.change_pct}
          isPositive={isMarketUp}
          prefix="₹"
          loading={loading}
        />

        <StatCard
          label="INDEX CHANGE"
          value={
            typeof indexData.change === 'number'
              ? Math.abs(indexData.change)
              : indexData.change
          }
          isPositive={isMarketUp}
          prefix={isMarketUp ? '+₹' : '-₹'}
          loading={loading}
        />

        <StatCard
          label="Market Sentiment"
          value={displayedSentiment}
          loading={loading}
        />

        <StatCard
          label="Active Stocks"
          value={`${activeStocks} / 50`}
          loading={loading}
        />

      </div>


      {/* ========================================================
          NIFTY CHART
          ======================================================== */}

      <Card className="p-6">

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">

          <div className="flex items-center gap-3">

            <h2 className="text-lg font-semibold text-[#111111]">
              NIFTY 50 Overview
            </h2>

            <Badge
              variant={
                isMarketUp
                  ? 'success'
                  : 'danger'
              }
            >
              {isMarketUp
                ? 'Market Up'
                : 'Market Down'}
            </Badge>

          </div>


          <div className="flex items-center gap-2">

            {ranges.map((range) => (
              <button
                key={range}
                onClick={() =>
                  setTimeRange(range)
                }
                className={`px-3 py-1 text-xs font-semibold rounded-full transition-colors ${timeRange === range
                  ? 'bg-[#111111] text-white'
                  : 'bg-transparent border border-[#E5E7EB] text-[#6B7280] hover:bg-[#F3F4F6]'
                  }`}
              >
                {range}
              </button>
            ))}

          </div>

        </div>


        <div className="h-[300px] w-full">

          {loading || chartLoading ? (

            <div className="w-full h-full flex items-center justify-center">

              <Loader2 className="w-8 h-8 animate-spin text-[#D1D5DB]" />

            </div>

          ) : chartError || chartData.length === 0 ? (

            <div className="w-full h-full flex items-center justify-center text-sm text-[#6B7280] text-center px-6">

              {chartError ||
                'Historical NIFTY data is currently unavailable.'}

            </div>

          ) : (

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <AreaChart
                data={chartData}
                margin={{
                  top: 10,
                  right: 10,
                  left: 10,
                  bottom: 0,
                }}
              >

                <defs>

                  <linearGradient
                    id="niftyAreaGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >

                    <stop
                      offset="5%"
                      stopColor={
                        isMarketUp
                          ? '#22C55E'
                          : '#EF4444'
                      }
                      stopOpacity={0.15}
                    />

                    <stop
                      offset="95%"
                      stopColor={
                        isMarketUp
                          ? '#22C55E'
                          : '#EF4444'
                      }
                      stopOpacity={0}
                    />

                  </linearGradient>

                </defs>


                <XAxis
                  dataKey="time"
                  tick={{
                    fontSize: 11,
                    fill: '#6B7280',
                  }}
                  axisLine={false}
                  tickLine={false}
                  minTickGap={30}
                />


                <YAxis
                  domain={['dataMin', 'dataMax']}
                  tick={{
                    fontSize: 11,
                    fill: '#6B7280',
                  }}
                  axisLine={false}
                  tickLine={false}
                  width={60}
                  tickFormatter={(value) =>
                    Number(value).toLocaleString(
                      'en-IN',
                      {
                        maximumFractionDigits: 0,
                      }
                    )
                  }
                />


                <Tooltip
                  content={<CustomTooltip />}
                  cursor={{
                    stroke: '#9CA3AF',
                    strokeWidth: 1,
                    strokeDasharray: '4 4',
                  }}
                />


                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={
                    isMarketUp
                      ? '#22C55E'
                      : '#EF4444'
                  }
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#niftyAreaGradient)"
                  isAnimationActive={false}
                  dot={false}
                  connectNulls={false}
                />

              </AreaChart>

            </ResponsiveContainer>

          )}

        </div>

      </Card>


      {/* ========================================================
          TOP MOVERS
          ======================================================== */}

      <Card className="p-0 overflow-hidden">

        <div className="px-6 py-5 border-b border-[#E5E7EB]">

          <h2 className="text-lg font-semibold text-[#111111]">
            Top Movers
          </h2>

        </div>


        <div className="overflow-x-auto">

          <table className="w-full text-sm text-left">

            <thead className="text-[11px] uppercase tracking-[0.08em] text-[#6B7280] bg-[#F7F8F5]">

              <tr>

                <th className="px-6 py-4 font-medium">
                  Name
                </th>

                <th className="px-6 py-4 font-medium">
                  Price
                </th>

                <th className="px-6 py-4 font-medium">
                  24h Change
                </th>

                <th className="px-6 py-4 font-medium text-right">
                  Action
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-[#E5E7EB]">

              {loading ? (

                <tr>

                  <td
                    colSpan="4"
                    className="px-6 py-8 text-center"
                  >
                    <Loader2 className="w-6 h-6 animate-spin text-[#D1D5DB] mx-auto" />
                  </td>

                </tr>

              ) : topMovers.length === 0 ? (

                <tr>

                  <td
                    colSpan="4"
                    className="px-6 py-8 text-center text-gray-500"
                  >
                    No active movers found.
                  </td>

                </tr>

              ) : (

                topMovers.map((stock) => {

                  const price = Number(
                    stock.price
                  );

                  const changePct = Number(
                    stock.change_pct
                  );

                  return (

                    <tr
                      key={stock.symbol}
                      className="hover:bg-[#F7F8F5] transition-colors duration-150"
                    >

                      <td className="px-6 py-4 font-semibold text-[#111111]">
                        {stock.symbol}
                      </td>


                      <td className="px-6 py-4 font-bold tabular-nums">

                        {Number.isFinite(price)
                          ? `₹${price.toLocaleString(
                            'en-IN',
                            {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            }
                          )}`
                          : 'Unavailable'}

                      </td>


                      <td
                        className={`px-6 py-4 font-semibold tabular-nums ${changePct >= 0
                          ? 'text-[#22C55E]'
                          : 'text-[#EF4444]'
                          }`}
                      >

                        {Number.isFinite(
                          changePct
                        )
                          ? `${changePct > 0
                            ? '+'
                            : ''
                          }${changePct.toFixed(2)}%`
                          : 'Unavailable'}

                      </td>


                      <td className="px-6 py-3 text-right">

                        <div className="flex justify-end gap-2">

                          <Button
                            variant="outline"
                            size="sm"
                            className="w-[60px]"
                            onClick={() =>
                            (window.location.href =
                              '/portfolio')
                            }
                          >
                            Sell
                          </Button>

                          <Button
                            variant="primary"
                            size="sm"
                            className="w-[60px]"
                            onClick={() =>
                            (window.location.href =
                              '/portfolio')
                            }
                          >
                            Buy
                          </Button>

                        </div>

                      </td>

                    </tr>

                  );
                })

              )}

            </tbody>

          </table>

        </div>

      </Card>

    </div>
  );
}