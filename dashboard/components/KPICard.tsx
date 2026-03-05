interface KPICardProps {
  title: string;
  value: string | number;
  icon: any;
  description?: string;
  trend?: {
    value: number;
    isUp: boolean;
  };
}

export default function KPICard({ title, value, icon: Icon, description, trend }: KPICardProps) {
  return (
    <div className="bg-white p-7 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
          <Icon size={26} />
        </div>
        {trend && (
          <span className={`text-sm font-medium px-2.5 py-1 rounded-full ${
            trend.isUp ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {trend.isUp ? '+' : '-'}{trend.value}%
          </span>
        )}
      </div>
      <div>
        <h3 className="text-base font-medium text-slate-500 mb-1">{title}</h3>
        <p className="text-3xl font-bold text-slate-900 tracking-tight">{value}</p>
        {description && <p className="text-sm text-slate-400 mt-2">{description}</p>}
      </div>
    </div>
  );
}
