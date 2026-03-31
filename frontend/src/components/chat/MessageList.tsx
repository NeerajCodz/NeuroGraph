import { motion } from 'framer-motion';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Bot, UserRound } from 'lucide-react';

const conversation = [
  {
    id: 'u-1',
    role: 'user' as const,
    text: 'Can you audit Q4 deployment risk for the enterprise tenant and highlight conflict clusters?',
  },
  {
    id: 'a-1',
    role: 'assistant' as const,
    text:
      'Sure. I traversed the memory graph and found three clusters with elevated conflict risk: Cluster Alpha in IAM policy ownership, Cluster Beta in infra rollout dependencies, and Cluster Delta in resource quota overlap.',
    meta: 'Graph traversal • 2.1s',
  },
  {
    id: 'u-2',
    role: 'user' as const,
    text: 'Focus on Cluster Beta and surface affected nodes with edge weights above 0.7.',
  },
  {
    id: 'a-2',
    role: 'assistant' as const,
    text:
      'Done. Nodes 184, 452, and 507 are above threshold. The strongest edge is between 452 and 507 at 0.84 confidence, indicating deployment orchestration contention between Alpha and Beta teams.',
    meta: 'Hybrid search + edge ranking',
  },
];

export default function MessageList() {
  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 py-4 md:py-6">
      {conversation.map((message, index) => {
        const isAssistant = message.role === 'assistant';

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
              'mt-0.5 h-8 w-8 ring-1 ' +
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
                <div className="text-sm leading-7 text-white/88">
                  {message.text}
                  {message.meta ? (
                    <p className="mt-2 text-[11px] uppercase tracking-[0.16em] text-purple-200/55">{message.meta}</p>
                  ) : null}
                </div>
              ) : (
                <div className="inline-block max-w-[95%] rounded-2xl border border-white/12 bg-white/6 px-4 py-2.5 text-left text-sm leading-relaxed text-white/92">
                  {message.text}
                </div>
              )}
            </div>
          </motion.article>
        );
      })}
    </div>
  );
}
