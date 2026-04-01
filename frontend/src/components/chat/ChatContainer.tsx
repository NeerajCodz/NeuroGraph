import MessageList from './MessageList';
import MessageInput from './MessageInput';

interface ChatContainerMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface ChatContainerProps {
  messages?: ChatContainerMessage[];
  onSend?: (message: string) => void;
  isLoading?: boolean;
}

export default function ChatContainer({
  messages = [],
  onSend = () => {},
  isLoading = false,
}: ChatContainerProps) {
  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden">
      <div className="scrollbar-thin flex-1 overflow-y-auto px-3 md:px-6">
        <MessageList messages={messages} />
      </div>

      <div className="shrink-0 border-t border-white/10 bg-black/15 px-3 py-3 backdrop-blur-md md:px-6 md:py-4">
        <MessageInput onSend={onSend} disabled={isLoading} />
      </div>
    </div>
  );
}
