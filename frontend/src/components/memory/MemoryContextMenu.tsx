import { Lock, Unlock, Copy, Trash2, Link2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ContextMenuProps {
  x: number;
  y: number;
  isLocked: boolean;
  onLock: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onConnect: () => void;
  onClose: () => void;
}

export default function MemoryContextMenu({
  x,
  y,
  isLocked,
  onLock,
  onDuplicate,
  onDelete,
  onConnect,
  onClose,
}: ContextMenuProps) {
  const menuItems = [
    {
      icon: isLocked ? Unlock : Lock,
      label: isLocked ? 'Unlock' : 'Lock',
      onClick: onLock,
      color: 'text-amber-400',
    },
    {
      icon: Copy,
      label: 'Duplicate',
      onClick: onDuplicate,
      color: 'text-blue-400',
    },
    {
      icon: Link2,
      label: 'Connect to...',
      onClick: onConnect,
      color: 'text-purple-400',
    },
    {
      icon: Trash2,
      label: 'Delete',
      onClick: onDelete,
      color: 'text-red-400',
      destructive: true,
    },
  ];

  return (
    <>
      {/* Backdrop to close menu */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
        onContextMenu={(e) => {
          e.preventDefault();
          onClose();
        }}
      />

      {/* Menu */}
      <div
        style={{ left: x, top: y }}
        className={cn(
          'fixed z-50 min-w-[160px] rounded-xl overflow-hidden',
          'bg-[#130b29]/95 border border-white/15 backdrop-blur-xl shadow-2xl',
          'animate-in fade-in-0 zoom-in-95 duration-150'
        )}
      >
        <div className="p-1">
          {menuItems.map((item) => (
            <button
              key={item.label}
              onClick={() => {
                item.onClick();
                onClose();
              }}
              className={cn(
                'flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-sm transition-colors',
                'text-white/80 hover:bg-white/10',
                item.destructive && 'hover:bg-red-500/20'
              )}
            >
              <item.icon className={cn('w-4 h-4', item.color)} />
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
