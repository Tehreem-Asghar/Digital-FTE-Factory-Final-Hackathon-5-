interface SentimentBarProps {
  score: number; // 0 to 1
}

export default function SentimentBar({ score }: SentimentBarProps) {
  const getColor = () => {
    if (score >= 0.7) return 'bg-green-500';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getLabel = () => {
    if (score >= 0.7) return 'Positive';
    if (score >= 0.4) return 'Neutral';
    return 'Negative';
  };

  return (
    <div className="flex flex-col w-full min-w-[80px]">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">{getLabel()}</span>
        <span className="text-xs font-mono font-bold text-slate-600">{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-50">
        <div 
          className={`h-full rounded-full transition-all duration-700 ${getColor()}`} 
          style={{ width: `${score * 100}%` }}
        />
      </div>
    </div>
  );
}
