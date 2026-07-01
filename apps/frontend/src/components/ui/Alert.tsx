import { ReactNode } from 'react';

interface AlertProps {
  variant: 'default' | 'destructive' | 'success';
  children: ReactNode;
}

export function Alert({ variant = 'default', children }: AlertProps) {
  const baseStyles = 'px-4 py-3 rounded border flex items-center gap-3 text-sm';
  const variantStyles = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    destructive: 'bg-red-50 border-red-200 text-red-800',
    success: 'bg-green-50 border-green-200 text-green-800',
  };

  return (
    <div className={`${baseStyles} ${variantStyles[variant]}`}>
      {children}
    </div>
  );
}
