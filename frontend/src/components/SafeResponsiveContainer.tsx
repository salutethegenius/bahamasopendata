'use client';

import {
  useEffect,
  useRef,
  useState,
  type ComponentProps,
  type CSSProperties,
} from 'react';
import { ResponsiveContainer as RechartsResponsiveContainer } from 'recharts';

type ResponsiveContainerProps = ComponentProps<typeof RechartsResponsiveContainer>;

function toStyleSize(value: ResponsiveContainerProps['width'] | ResponsiveContainerProps['height']) {
  if (typeof value === 'number') {
    return `${value}px`;
  }

  return value;
}

export default function SafeResponsiveContainer({
  children,
  width = '100%',
  height = '100%',
  minWidth,
  minHeight,
  ...props
}: ResponsiveContainerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hasMeasuredSize, setHasMeasuredSize] = useState(false);

  useEffect(() => {
    const node = containerRef.current;

    if (!node) {
      return undefined;
    }

    const updateSize = () => {
      const { width: measuredWidth, height: measuredHeight } = node.getBoundingClientRect();
      setHasMeasuredSize(measuredWidth > 0 && measuredHeight > 0);
    };

    updateSize();

    const observer = new ResizeObserver(() => {
      updateSize();
    });

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, []);

  const wrapperStyle: CSSProperties = {
    width: toStyleSize(width),
    height: toStyleSize(height),
    minWidth,
    minHeight,
  };

  return (
    <div ref={containerRef} className="min-w-0" style={wrapperStyle}>
      {hasMeasuredSize ? (
        <RechartsResponsiveContainer
          width="100%"
          height="100%"
          minWidth={minWidth}
          minHeight={minHeight}
          {...props}
        >
          {children}
        </RechartsResponsiveContainer>
      ) : null}
    </div>
  );
}
