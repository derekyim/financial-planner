import type { Step, CallBackProps, STATUS_EVENTS } from 'react-joyride';

const STORAGE_KEY = 'dp-tour-completed';

export type TourId = 'main';

export type TourDefinition = {
  id: TourId;
  steps: Step[];
};

const MAIN_TOUR: TourDefinition = {
  id: 'main',
  steps: [
    {
      target: 'body',
      content:
        'Welcome to Dysprosium Financial Planner! This quick tour will show you the key areas of the application.',
      placement: 'center',
      disableBeacon: true,
    },
    {
      target: '[data-tour="nav-sidebar"]',
      content:
        'Use the left navigation to move between sections. Each section maps to a certification requirement.',
      placement: 'right',
    },
    {
      target: '[data-tour="nav-agent"]',
      content:
        'The Agent page is your main workspace. Chat with the AI financial planner to analyze your spreadsheet model.',
      placement: 'right',
    },
    {
      target: '[data-tour="nav-documentation"]',
      content:
        'Documentation covers the RAG application, evaluation approach, and next steps for Demo Day.',
      placement: 'right',
    },
    {
      target: '[data-tour="nav-evals"]',
      content:
        'The Evals section shows RAGAS evaluation results and improvements made based on evaluation feedback.',
      placement: 'right',
    },
    {
      target: '[data-tour="nav-architecture"]',
      content:
        'The Architecture page shows the full system diagram and how all components fit together.',
      placement: 'right',
    },
  ],
};

const TOURS: Record<TourId, TourDefinition> = {
  main: MAIN_TOUR,
};

class TourEngine {
  private completedTours: Set<string>;

  constructor() {
    this.completedTours = new Set();
    this.loadState();
  }

  private loadState(): void {
    if (typeof window === 'undefined') return;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as string[];
        this.completedTours = new Set(parsed);
      }
    } catch {
      this.completedTours = new Set();
    }
  }

  private saveState(): void {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(Array.from(this.completedTours)),
      );
    } catch {
      // localStorage may be unavailable
    }
  }

  getTour(tourId: TourId): TourDefinition {
    return TOURS[tourId];
  }

  getSteps(tourId: TourId): Step[] {
    return TOURS[tourId]?.steps ?? [];
  }

  isCompleted(tourId: TourId): boolean {
    return this.completedTours.has(tourId);
  }

  shouldAutoStart(tourId: TourId): boolean {
    return !this.isCompleted(tourId);
  }

  markCompleted(tourId: TourId): void {
    this.completedTours.add(tourId);
    this.saveState();
  }

  reset(tourId?: TourId): void {
    if (tourId) {
      this.completedTours.delete(tourId);
    } else {
      this.completedTours.clear();
    }
    this.saveState();
  }

  handleCallback(tourId: TourId, data: CallBackProps): void {
    const finishedStatuses: string[] = ['finished', 'skipped'];
    if (finishedStatuses.includes(data.status)) {
      this.markCompleted(tourId);
    }
  }
}

export const tourEngine = new TourEngine();
