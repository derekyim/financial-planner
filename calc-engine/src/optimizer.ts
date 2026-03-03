import { CalcEngine, CellRef, CellSetOp, CellResult } from "./engine";

export interface LeverSpec {
  sheet: string;
  col: number;
  row: number;
  min: number;
  max: number;
  /** Number of discrete steps between min and max (default 10) */
  steps?: number;
  label?: string;
}

export interface TargetConstraint {
  sheet: string;
  col: number;
  row: number;
  operator: ">=" | "<=" | "==" | ">" | "<";
  value: number;
  label?: string;
}

export interface OptimizeRequest {
  levers: LeverSpec[];
  targets: TargetConstraint[];
  /** Cell to maximize (or minimize with negative weight) */
  objective: CellRef & { label?: string };
  /** "maximize" or "minimize" */
  direction?: "maximize" | "minimize";
  /** Number of random samples (default 500) */
  samples?: number;
  /** Number of top solutions to return (default 5) */
  topN?: number;
  /** Additional cells to read in each solution */
  extraReads?: (CellRef & { label?: string })[];
}

export interface Solution {
  rank: number;
  objectiveValue: number;
  leverValues: { label: string; value: number; sheet: string; col: number; row: number }[];
  targetResults: { label: string; value: number; met: boolean; constraint: string }[];
  extraValues?: { label: string; value: number }[];
}

export interface OptimizeResult {
  solutions: Solution[];
  totalSampled: number;
  feasibleCount: number;
}

function latinHypercubeSamples(
  levers: LeverSpec[],
  n: number
): number[][] {
  const d = levers.length;
  const samples: number[][] = [];

  const permutations: number[][] = [];
  for (let j = 0; j < d; j++) {
    const perm = Array.from({ length: n }, (_, i) => i);
    for (let i = n - 1; i > 0; i--) {
      const k = Math.floor(Math.random() * (i + 1));
      [perm[i], perm[k]] = [perm[k], perm[i]];
    }
    permutations.push(perm);
  }

  for (let i = 0; i < n; i++) {
    const point: number[] = [];
    for (let j = 0; j < d; j++) {
      const bin = permutations[j][i];
      const u = (bin + Math.random()) / n;
      const { min, max } = levers[j];
      point.push(min + u * (max - min));
    }
    samples.push(point);
  }

  return samples;
}

function checkConstraint(value: number, op: string, target: number): boolean {
  switch (op) {
    case ">=": return value >= target;
    case "<=": return value <= target;
    case ">":  return value > target;
    case "<":  return value < target;
    case "==": return Math.abs(value - target) < 1e-6;
    default:   return false;
  }
}

function formatConstraint(op: string, value: number): string {
  return `${op} ${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

export function optimize(
  engine: CalcEngine,
  request: OptimizeRequest
): OptimizeResult {
  const {
    levers,
    targets,
    objective,
    direction = "maximize",
    samples: nSamples = 500,
    topN = 5,
    extraReads = [],
  } = request;

  const readCells: CellRef[] = [
    { sheet: objective.sheet, col: objective.col, row: objective.row },
    ...targets.map((t) => ({ sheet: t.sheet, col: t.col, row: t.row })),
    ...extraReads.map((e) => ({ sheet: e.sheet, col: e.col, row: e.row })),
  ];

  const leverRefs = levers.map((l) => ({
    sheet: l.sheet,
    col: l.col,
    row: l.row,
  }));
  const originals = engine.snapshot(leverRefs);

  const samplePoints = latinHypercubeSamples(levers, nSamples);

  const feasibleSolutions: {
    score: number;
    leverVals: number[];
    results: CellResult[];
  }[] = [];

  try {
    for (const point of samplePoints) {
      const sets: CellSetOp[] = levers.map((l, i) => ({
        sheet: l.sheet,
        col: l.col,
        row: l.row,
        value: Math.round(point[i] * 100) / 100,
      }));

      engine.setCells(sets);
      const results = engine.getCellValues(readCells);

      const objVal = results[0].value as number;
      if (typeof objVal !== "number" || isNaN(objVal)) continue;

      let allMet = true;
      for (let t = 0; t < targets.length; t++) {
        const tVal = results[1 + t].value as number;
        if (typeof tVal !== "number" || !checkConstraint(tVal, targets[t].operator, targets[t].value)) {
          allMet = false;
          break;
        }
      }

      if (allMet) {
        feasibleSolutions.push({
          score: direction === "maximize" ? objVal : -objVal,
          leverVals: point.map((v) => Math.round(v * 100) / 100),
          results,
        });
      }
    }
  } finally {
    engine.setCells(originals);
  }

  feasibleSolutions.sort((a, b) => b.score - a.score);
  const top = feasibleSolutions.slice(0, topN);

  const solutions: Solution[] = top.map((sol, idx) => ({
    rank: idx + 1,
    objectiveValue: direction === "maximize" ? sol.score : -sol.score,
    leverValues: levers.map((l, i) => ({
      label: l.label ?? `Lever ${i + 1}`,
      value: sol.leverVals[i],
      sheet: l.sheet,
      col: l.col,
      row: l.row,
    })),
    targetResults: targets.map((t, i) => ({
      label: t.label ?? `Target ${i + 1}`,
      value: sol.results[1 + i].value as number,
      met: checkConstraint(sol.results[1 + i].value as number, t.operator, t.value),
      constraint: formatConstraint(t.operator, t.value),
    })),
    extraValues: extraReads.map((e, i) => ({
      label: e.label ?? `Extra ${i + 1}`,
      value: sol.results[1 + targets.length + i].value as number,
    })),
  }));

  return {
    solutions,
    totalSampled: nSamples,
    feasibleCount: feasibleSolutions.length,
  };
}
