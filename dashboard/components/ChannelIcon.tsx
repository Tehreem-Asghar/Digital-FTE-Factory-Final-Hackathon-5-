import { Mail, MessageCircle, Layout, Globe } from 'lucide-react';

interface ChannelIconProps {
  channel: string;
  size?: number;
}

export default function ChannelIcon({ channel, size = 18 }: ChannelIconProps) {
  const getIcon = () => {
    switch (channel.toLowerCase()) {
      case 'email':
      case 'gmail':
        return <Mail size={size} className="text-blue-500" />;
      case 'whatsapp':
        return <MessageCircle size={size} className="text-green-500" />;
      case 'web_form':
      case 'support_form':
        return <Layout size={size} className="text-purple-500" />;
      default:
        return <Globe size={size} className="text-slate-500" />;
    }
  };

  return <div className="inline-flex items-center justify-center" title={channel}>{getIcon()}</div>;
}
