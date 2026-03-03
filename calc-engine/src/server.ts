import express, { Request, Response } from "express";
import { CalcEngine, SheetData, CellRef, CellSetOp } from "./engine";
import { optimize, OptimizeRequest } from "./optimizer";

const app = express();
app.use(express.json({ limit: "50mb" }));

const engine = new CalcEngine();

app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok", loaded: engine.isLoaded() });
});

/**
 * POST /load
 * Body: { sheets: [{ name: string, data: (string|number|null)[][] }] }
 */
app.post("/load", (req: Request, res: Response) => {
  try {
    const { sheets } = req.body as { sheets: SheetData[] };
    if (!sheets || !Array.isArray(sheets)) {
      res.status(400).json({ error: "Body must include 'sheets' array" });
      return;
    }

    const result = engine.loadModel(sheets);
    console.log(`[CalcEngine] Loaded ${result.sheets} sheets, ${result.cells} cells`);

    res.json({
      ok: true,
      sheets: result.sheets,
      cells: result.cells,
      sheetNames: engine.getSheetNames(),
    });
  } catch (err: any) {
    console.error("[CalcEngine] Load error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * POST /calculate
 * Body: { sets: CellSetOp[], reads: CellRef[] }
 * Sets cells temporarily, reads results, restores originals.
 */
app.post("/calculate", (req: Request, res: Response) => {
  try {
    if (!engine.isLoaded()) {
      res.status(400).json({ error: "No model loaded. POST /load first." });
      return;
    }

    const { sets, reads } = req.body as { sets: CellSetOp[]; reads: CellRef[] };
    if (!sets || !reads) {
      res.status(400).json({ error: "Body must include 'sets' and 'reads'" });
      return;
    }

    const results = engine.calculateWith(sets, reads);
    res.json({ ok: true, results });
  } catch (err: any) {
    console.error("[CalcEngine] Calculate error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * POST /optimize
 * Body: OptimizeRequest
 */
app.post("/optimize", (req: Request, res: Response) => {
  try {
    if (!engine.isLoaded()) {
      res.status(400).json({ error: "No model loaded. POST /load first." });
      return;
    }

    const request = req.body as OptimizeRequest;
    if (!request.levers || !request.objective) {
      res.status(400).json({ error: "Body must include 'levers' and 'objective'" });
      return;
    }

    if (!request.targets) {
      request.targets = [];
    }

    console.log(
      `[CalcEngine] Optimizing: ${request.levers.length} levers, ` +
      `${request.targets.length} constraints, ` +
      `${request.samples ?? 500} samples`
    );

    const startTime = Date.now();
    const result = optimize(engine, request);
    const elapsed = Date.now() - startTime;

    console.log(
      `[CalcEngine] Done in ${elapsed}ms: ${result.feasibleCount}/${result.totalSampled} feasible`
    );

    res.json({ ok: true, elapsed_ms: elapsed, ...result });
  } catch (err: any) {
    console.error("[CalcEngine] Optimize error:", err.message);
    res.status(500).json({ error: err.message });
  }
});

const PORT = parseInt(process.env.CALC_ENGINE_PORT || "4100", 10);

app.listen(PORT, () => {
  console.log(`[CalcEngine] Listening on http://localhost:${PORT}`);
});
