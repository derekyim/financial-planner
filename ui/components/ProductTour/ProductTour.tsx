import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import type { CallBackProps } from 'react-joyride';
import { tourEngine } from '@/services/TourEngine';

const Joyride = dynamic(() => import('react-joyride'), { ssr: false });

export default function ProductTour() {
  const [run, setRun] = useState(false);
  const steps = tourEngine.getSteps('main');

  const startTour = useCallback(() => {
    setRun(true);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (tourEngine.shouldAutoStart('main')) {
        setRun(true);
      }
    }, 1500);

    window.addEventListener('start-tour', startTour);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('start-tour', startTour);
    };
  }, [startTour]);

  function handleCallback(data: CallBackProps) {
    tourEngine.handleCallback('main', data);
    const finishedStatuses: string[] = ['finished', 'skipped'];
    if (finishedStatuses.includes(data.status)) {
      setRun(false);
    }
  }

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showSkipButton
      showProgress
      callback={handleCallback}
      styles={{
        options: {
          primaryColor: '#4285F4',
          zIndex: 10000,
        },
        tooltipContainer: {
          textAlign: 'left' as const,
        },
      }}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Finish',
        next: 'Next',
        skip: 'Skip Tour',
      }}
    />
  );
}
