import { HyperFormula, SimpleCellAddress, CellValue } from "hyperformula";

export interface SheetData {
  name: string;
  data: (string | number | null)[][];
}

export interface CellRef {
  sheet: string;
  col: number;
  row: number;
}

export interface CellSetOp {
  sheet: string;
  col: number;
  row: number;
  value: string | number | null;
}

export interface CellResult {
  sheet: string;
  col: number;
  row: number;
  value: CellValue;
}

export class CalcEngine {
  private hf: HyperFormula | null = null;
  private sheetNameToId: Map<string, number> = new Map();

  isLoaded(): boolean {
    return this.hf !== null;
  }

  loadModel(sheets: SheetData[]): { sheets: number; cells: number } {
    if (this.hf) {
      this.hf.destroy();
    }

    const sheetsObj: Record<string, (string | number | null)[][]> = {};
    for (const s of sheets) {
      sheetsObj[s.name] = s.data;
    }

    this.hf = HyperFormula.buildFromSheets(sheetsObj, {
      licenseKey: "gpl-v3",
    });

    this.sheetNameToId.clear();
    let totalCells = 0;
    for (const s of sheets) {
      const id = this.hf.getSheetId(s.name);
      if (id !== undefined) {
        this.sheetNameToId.set(s.name, id);
        const dims = this.hf.getSheetDimensions(id);
        totalCells += dims.width * dims.height;
      }
    }

    return { sheets: sheets.length, cells: totalCells };
  }

  private resolveSheet(name: string): number {
    const id = this.sheetNameToId.get(name);
    if (id === undefined) {
      throw new Error(`Sheet '${name}' not found. Available: ${[...this.sheetNameToId.keys()].join(", ")}`);
    }
    return id;
  }

  private addr(ref: CellRef): SimpleCellAddress {
    return { sheet: this.resolveSheet(ref.sheet), col: ref.col, row: ref.row };
  }

  getCellValue(ref: CellRef): CellValue {
    if (!this.hf) throw new Error("No model loaded");
    return this.hf.getCellValue(this.addr(ref));
  }

  getCellValues(refs: CellRef[]): CellResult[] {
    if (!this.hf) throw new Error("No model loaded");
    return refs.map((ref) => ({
      ...ref,
      value: this.hf!.getCellValue(this.addr(ref)),
    }));
  }

  setCells(ops: CellSetOp[]): void {
    if (!this.hf) throw new Error("No model loaded");
    this.hf.batch(() => {
      for (const op of ops) {
        const addr = this.addr(op);
        this.hf!.setCellContents(addr, [[op.value]]);
      }
    });
  }

  /**
   * Snapshot the current values of the given cells so they can be restored later.
   */
  snapshot(refs: CellRef[]): CellSetOp[] {
    if (!this.hf) throw new Error("No model loaded");
    return refs.map((ref) => {
      const addr = this.addr(ref);
      const formula = this.hf!.getCellFormula(addr);
      const value = formula ?? this.hf!.getCellValue(addr);
      return { ...ref, value: value as string | number | null };
    });
  }

  /**
   * Set cells, read results, then restore originals — all in memory.
   * Returns the read values after the temporary changes.
   */
  calculateWith(
    sets: CellSetOp[],
    reads: CellRef[]
  ): CellResult[] {
    if (!this.hf) throw new Error("No model loaded");

    const originals = this.snapshot(
      sets.map((s) => ({ sheet: s.sheet, col: s.col, row: s.row }))
    );

    try {
      this.setCells(sets);
      return this.getCellValues(reads);
    } finally {
      this.setCells(originals);
    }
  }

  getSheetNames(): string[] {
    return [...this.sheetNameToId.keys()];
  }

  getSheetDimensions(sheetName: string): { width: number; height: number } {
    if (!this.hf) throw new Error("No model loaded");
    return this.hf.getSheetDimensions(this.resolveSheet(sheetName));
  }

  destroy(): void {
    if (this.hf) {
      this.hf.destroy();
      this.hf = null;
      this.sheetNameToId.clear();
    }
  }
}
