import { useSprings, animated } from '@react-spring/web';
import { useEffect, useRef, useState } from 'react';

type SplitTextProps = {
  text: string;
  className?: string;
  delay?: number;
  trailing?: boolean;
};

export const SplitText = ({ text, className = '', delay = 100, trailing = false }: SplitTextProps) => {
  const words = text.split(' ');
  const [inView, setInView] = useState(false);
  const ref = useRef<HTMLParagraphElement | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]: IntersectionObserverEntry[]) => {
        if (entry.isIntersecting) {
          setInView(true);

          if (ref.current) {
            observer.unobserve(ref.current);
          }
        }
      },
      { threshold: 0.1, rootMargin: '-10px' }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  const [springs] = useSprings(
    words.length,
    (index) => ({
      from: { opacity: 0, transform: 'translate3d(0,40px,0)' },
      to: inView
        ? { opacity: 1, transform: 'translate3d(0,0px,0)' }
        : { opacity: 0, transform: 'translate3d(0,40px,0)' },
      delay: index * delay,
      config: { mass: 1, tension: 170, friction: 26 },
    }),
    [inView, delay, words.length]
  );

  return (
    <p className={className} ref={ref}>
      {springs.map((springStyle, index) => (
        <animated.span
          key={index}
          style={springStyle}
          className="inline-block will-change-[opacity,transform]"
        >
          {words[index]}
          {(trailing || index < words.length - 1) ? '\u00a0' : ''}
        </animated.span>
      ))}
    </p>
  );
};
