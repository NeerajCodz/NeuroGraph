import { useState } from 'react';
import { X, Link2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface EdgeDialogProps {
  sourceContent: string;
  targetContent: string;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function EdgeReasonDialog({
  sourceContent,
  targetContent,
  onConfirm,
  onCancel,
  isLoading,
}: EdgeDialogProps) {
  const [reason, setReason] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm(reason.trim());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        className={cn(
          'w-full max-w-lg mx-4 rounded-2xl overflow-hidden',
          'bg-[#130b29]/95 border border-white/15 backdrop-blur-xl shadow-2xl',
          'animate-in fade-in-0 zoom-in-95 duration-200'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div className="flex items-center gap-2 text-white">
            <Link2 className="w-5 h-5 text-purple-400" />
            <h3 className="font-semibold">Connect Memories</h3>
          </div>
          <button
            onClick={onCancel}
            className="p-1 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          {/* Memory previews */}
          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20">
              <p className="text-[10px] uppercase tracking-wider text-purple-300/60 mb-1">From</p>
              <p className="text-sm text-white/80 line-clamp-2">{sourceContent}</p>
            </div>
            
            <div className="flex justify-center">
              <div className="w-px h-6 bg-gradient-to-b from-purple-500/40 to-fuchsia-500/40" />
            </div>
            
            <div className="p-3 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20">
              <p className="text-[10px] uppercase tracking-wider text-fuchsia-300/60 mb-1">To</p>
              <p className="text-sm text-white/80 line-clamp-2">{targetContent}</p>
            </div>
          </div>

          {/* Reason input */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-2">
                Reasoning (optional)
              </label>
              <Input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Why are these memories connected?"
                className="bg-black/30 border-white/10 text-white placeholder:text-white/30"
                disabled={isLoading}
                autoFocus
              />
              <p className="mt-1.5 text-[11px] text-white/40">
                Add context to explain the relationship between these memories
              </p>
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isLoading}
                className="border-white/20 text-white hover:bg-white/10"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="bg-gradient-to-r from-purple-500 to-fuchsia-500 hover:from-purple-600 hover:to-fuchsia-600 text-white"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Link2 className="w-4 h-4 mr-2" />
                    Connect
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
