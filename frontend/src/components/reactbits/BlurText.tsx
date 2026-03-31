import { useRef, useEffect, useState } from 'react';
import { useSprings, animated } from '@react-spring/web';

interface BlurTextProps {
  text: string;
  delay?: number;
  className?: string;
  animateBy?: 'words' | 'letters';
  direction?: 'top' | 'bottom';
}

export const BlurText: React.FC<BlurTextProps> = ({
  text,
  delay = 200,
  className = '',
  animateBy = 'words',
  direction = 'top',
}) => {
  const elements = animateBy === 'words' ? text.split(' ') : text.split('');
  const [inView, setInView] = useState(false);
  const ref = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.unobserve(ref.current!);
        }
      },
      { threshold: 0.1 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const springs = useSprings(
    elements.length,
    elements.map((_, i) => ({
      from: { 
        filter: 'blur(10px)', 
        opacity: 0, 
        transform: direction === 'top' ? 'translate3d(0,-50px,0)' : 'translate3d(0,50px,0)' 
      },
      to: inView
        ? { filter: 'blur(0px)', opacity: 1, transform: 'translate3d(0,0,0)' }
        : { filter: 'blur(10px)', opacity: 0, transform: direction === 'top' ? 'translate3d(0,-50px,0)' : 'translate3d(0,50px,0)' },
      delay: i * delay,
    }))
  );

  return (
    <p ref={ref} className={className}>
      {springs.map((props, index) => (
        <animated.span
          key={index}
          style={props}
          className="inline-block transition-transform will-change-[opacity,filter,transform]"
        >
          {elements[index] === ' ' ? '\u00A0' : elements[index]}
          {animateBy === 'words' && index < elements.length - 1 && '\u00A0'}
        </animated.span>
      ))}
    </p>
  );
};
