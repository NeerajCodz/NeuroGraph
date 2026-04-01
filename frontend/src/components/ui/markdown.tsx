import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownProps {
  content: string;
  className?: string;
}

export function Markdown({ content, className = '' }: MarkdownProps) {
  return (
    <div className={`prose prose-invert prose-sm max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Style code blocks
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="bg-white/10 px-1.5 py-0.5 rounded text-purple-200 text-[13px]" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={`${className} block bg-black/30 p-3 rounded-lg overflow-x-auto text-[13px]`} {...props}>
                {children}
              </code>
            );
          },
          // Style pre blocks
          pre: ({ children }) => (
            <pre className="bg-black/30 rounded-lg overflow-hidden my-2">
              {children}
            </pre>
          ),
          // Style links
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 underline">
              {children}
            </a>
          ),
          // Style lists
          ul: ({ children }) => (
            <ul className="list-disc list-inside space-y-1 my-2 text-white/80">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside space-y-1 my-2 text-white/80">
              {children}
            </ol>
          ),
          // Style headings
          h1: ({ children }) => <h1 className="text-xl font-bold text-white mt-4 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold text-white mt-3 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-semibold text-white mt-2 mb-1">{children}</h3>,
          // Style blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-purple-500/50 pl-3 my-2 text-white/70 italic">
              {children}
            </blockquote>
          ),
          // Style tables
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full border border-white/10 rounded-lg overflow-hidden">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="bg-white/5 px-3 py-2 text-left text-xs font-semibold text-white/70 border-b border-white/10">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 text-sm text-white/80 border-b border-white/5">
              {children}
            </td>
          ),
          // Style paragraphs
          p: ({ children }) => <p className="my-1.5 text-white/90">{children}</p>,
          // Style strong/bold
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          // Style emphasis/italic
          em: ({ children }) => <em className="italic text-white/80">{children}</em>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
