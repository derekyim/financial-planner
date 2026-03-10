import type { VercelRequest, VercelResponse } from "@vercel/node";
import { CalcEngine, SheetData } from "../src/engine";
import { optimize, OptimizeRequest } from "../src/optimizer";

const engine = new CalcEngine();

export default function handler(req: VercelRequest, res: VercelResponse) {
  const path = (req.query.path as string) || "";
  const route = `/${path}`.replace(/\/+/g, "/");

  if (req.method === "GET" && route === "/health") {
    return res.json({ status: "ok", loaded: engine.isLoaded() });
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    if (route === "/load") {
      const { sheets } = req.body as { sheets: SheetData[] };
      if (!sheets || !Array.isArray(sheets)) {
        return res.status(400).json({ error: "Body must include 'sheets' array" });
      }
      const result = engine.loadModel(sheets);
      console.log(`[CalcEngine] Loaded ${result.sheets} sheets, ${result.cells} cells`);
      return res.json({ ok: true, ...result, sheetNames: engine.getSheetNames() });
    }

    if (route === "/calculate") {
      if (!engine.isLoaded()) {
        return res.status(400).json({ error: "No model loaded. POST /load first." });
      }
      const { sets, reads } = req.body;
      if (!sets || !reads) {
        return res.status(400).json({ error: "Body must include 'sets' and 'reads'" });
      }
      const results = engine.calculateWith(sets, reads);
      return res.json({ ok: true, results });
    }

    if (route === "/optimize") {
      if (!engine.isLoaded()) {
        return res.status(400).json({ error: "No model loaded. POST /load first." });
      }
      const request = req.body as OptimizeRequest;
      if (!request.levers || !request.objective) {
        return res.status(400).json({ error: "Body must include 'levers' and 'objective'" });
      }
      if (!request.targets) request.targets = [];

      console.log(
        `[CalcEngine] Optimizing: ${request.levers.length} levers, ` +
        `${request.targets.length} constraints, ${request.samples ?? 500} samples`
      );

      const startTime = Date.now();
      const result = optimize(engine, request);
      const elapsed = Date.now() - startTime;

      console.log(`[CalcEngine] Done in ${elapsed}ms: ${result.feasibleCount}/${result.totalSampled} feasible`);
      return res.json({ ok: true, elapsed_ms: elapsed, ...result });
    }

    return res.status(404).json({ error: `Unknown route: ${route}` });
  } catch (err: any) {
    console.error(`[CalcEngine] Error on ${route}:`, err.message);
    return res.status(500).json({ error: err.message });
  }
}
