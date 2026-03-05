interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const getStyles = () => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'escalated':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'resolved':
      case 'closed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'pending':
      case 'in-progress':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getStyles()}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
