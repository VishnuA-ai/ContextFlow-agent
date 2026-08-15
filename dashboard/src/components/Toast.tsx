import { useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, X } from 'lucide-react';
import { useDashboardStore } from '../store';
import type { Toast } from '../types';

export function ToastContainer() {
  const { toasts, removeToast } = useDashboardStore();

  useEffect(() => {
    const timers = toasts.map((toast) => 
      setTimeout(() => {
        removeToast(toast.id);
      }, 5000)
    );

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [toasts, removeToast]);

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onClose: () => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  const config = {
    success: {
      icon: CheckCircle,
      bgColor: 'bg-green-500/20',
      borderColor: 'border-green-500/50',
      textColor: 'text-green-400',
      iconColor: 'text-green-400',
    },
    error: {
      icon: XCircle,
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/50',
      textColor: 'text-red-400',
      iconColor: 'text-red-400',
    },
    warning: {
      icon: AlertTriangle,
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/50',
      textColor: 'text-yellow-400',
      iconColor: 'text-yellow-400',
    },
  };

  const { icon: Icon, bgColor, borderColor, textColor, iconColor } = config[toast.type];

  return (
    <div
      className={`glass ${bgColor} ${borderColor} border rounded-lg p-4 flex items-start gap-3 min-w-[300px] animate-fade-in`}
    >
      <Icon size={20} className={iconColor} />
      <div className="flex-1">
        <p className={`text-sm font-medium ${textColor}`}>{toast.message}</p>
      </div>
      <button
        onClick={onClose}
        className={`text-gray-400 hover:text-white transition-colors`}
      >
        <X size={16} />
      </button>
    </div>
  );
}
