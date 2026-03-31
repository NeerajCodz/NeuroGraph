import { useState, type KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function MessageInput() {
  const [value, setValue] = useState('');

  const handleSend = () => {
    if (!value.trim()) return;
    setValue('');
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          className="max-h-36 min-h-11 w-full resize-y rounded-xl border border-white/12 bg-[#120b21] px-4 py-2.5 text-[15px] leading-6 text-white outline-none placeholder:text-white/35 focus:border-purple-300/40"
          placeholder="Ask NeuroGraph, inspect conflicts, or traverse memory..."
        />

        <Button
          size="icon"
          onClick={handleSend}
          disabled={!value.trim()}
          className="gradient-primary h-11 w-11 shrink-0 rounded-xl text-primary-foreground shadow-[0_18px_30px_-16px_rgba(166,108,255,0.95)] transition-all hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:opacity-45"
        >
          <Send className="h-4.5 w-4.5" />
        </Button>
      </div>
    </div>
  );
}

