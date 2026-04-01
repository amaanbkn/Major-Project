import { useState, useEffect, useRef } from 'react';

export const usePriceFlash = (price) => {
  const [flashClass, setFlashClass] = useState('');
  const prevPriceRef = useRef(price);

  useEffect(() => {
    if (price > prevPriceRef.current) {
      setFlashClass('animate-flash-green');
    } else if (price < prevPriceRef.current) {
      setFlashClass('animate-flash-red');
    }
    
    prevPriceRef.current = price;

    const timer = setTimeout(() => {
      setFlashClass('');
    }, 600);

    return () => clearTimeout(timer);
  }, [price]);

  return flashClass;
};
