import { motion } from 'framer-motion';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Bot, UserRound, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface ProcessingStep {
  step_number: number;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
  reasoning?: string;
  duration_ms?: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning_path?: Array<{ step: number; action: string; result: string }> | null;
  sources?: Array<{ content: string; layer: string; score: number }> | null;
  confidence?: number;
  created_at: string;
  processing_steps?: ProcessingStep[];
}

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

  const toggleSteps = (messageId: string) => {
    setExpandedSteps(prev => ({ ...prev, [messageId]: !prev[messageId] }));
  };

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="mb-6 p-6 rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
          <Bot className="w-10 h-10 text-purple-300" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-3">
          Start a Conversation
        </h2>
        <p className="text-white/60 max-w-md">
          Ask anything about your knowledge graph, traverse memory, or explore relationships.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 py-4 md:py-6">
      {messages.map((message, index) => {
        const isAssistant = message.role === 'assistant';
        const hasSteps = message.processing_steps && message.processing_steps.length > 0;
        const isExpanded = expandedSteps[message.id];

        return (
          <motion.article
            key={message.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, duration: 0.28 }}
            className={
              'flex w-full gap-3 ' +
              (isAssistant ? 'items-start' : 'flex-row-reverse items-start')
            }
          >
            <Avatar className={
              'mt-0.5 h-8 w-8 ring-1 shrink-0 ' +
              (isAssistant ? 'ring-purple-300/40 bg-purple-100/5' : 'ring-white/20 bg-white/10')
            }>
              <AvatarImage src="" />
              <AvatarFallback className={isAssistant ? 'bg-purple-300/15 text-purple-100' : 'bg-white/10 text-white/90'}>
                {isAssistant ? <Bot className="size-4" /> : <UserRound className="size-4" />}
              </AvatarFallback>
            </Avatar>

            <div className={'min-w-0 flex-1 ' + (isAssistant ? '' : 'text-right')}>
              <p className="mb-1 text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">
                {isAssistant ? 'NeuroGraph' : 'You'}
              </p>

              {isAssistant ? (
                <div className="space-y-3">
                  {/* Processing Steps */}
                  {hasSteps && (
                    <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 overflow-hidden">
                      <button
                        onClick={() => toggleSteps(message.id)}
                        className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-purple-500/10 transition-colors"
                      >
                        <span className="text-purple-200 font-medium">
                          Processing Steps ({message.processing_steps!.length})
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-white/40" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-white/40" />
                        )}
                      </button>
                      
                      {isExpanded && (
                        <div className="px-3 pb-3 space-y-2 border-t border-purple-500/10 pt-2">
                          {message.processing_steps!.map((step) => (
                            <div key={step.step_number} className="space-y-1">
                              <div className="flex items-center gap-2 text-xs">
                                <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                                  step.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                  step.status === 'running' ? 'bg-purple-500/20 text-purple-400' :
                                  step.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                  'bg-white/5 text-white/30'
                                }`}>
                                  {step.status === 'completed' ? '✓' : step.status === 'failed' ? '✗' : step.step_number}
                                </span>
                                <span className="text-white/70 font-medium">{step.action}</span>
                                {step.duration_ms && (
                                  <span className="text-white/30 ml-auto">{step.duration_ms}ms</span>
                                )}
                              </div>
                              {step.reasoning && (
                                <p className="text-[11px] text-white/50 ml-7">
                                  {step.reasoning}
                                </p>
                              )}
                              {step.result && (
                                <p className="text-[11px] text-purple-200/60 ml-7">
                                  → {step.result}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Response Content */}
                  <div className="text-sm leading-7 text-white/88">
                    {message.content}
                  </div>

                  {/* Metadata */}
                  {(message.confidence || message.sources) && (
                    <div className="flex items-center gap-3 text-[11px] text-white/40">
                      {message.confidence && (
                        <span>Confidence: {(message.confidence * 100).toFixed(0)}%</span>
                      )}
                      {message.sources && message.sources.length > 0 && (
                        <span>{message.sources.length} sources</span>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="inline-block max-w-[95%] rounded-2xl border border-white/12 bg-white/6 px-4 py-2.5 text-left text-sm leading-relaxed text-white/92">
                  {message.content}
                </div>
              )}
            </div>
          </motion.article>
        );
      })}
    </div>
  );
}
