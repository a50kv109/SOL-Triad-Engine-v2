# SOL-Triad visual prototype

This React/TypeScript application is a standalone visual prototype. Its evaluator is implemented in `src/services/engineService.ts`; it does not import, invoke, or validate the Python `sol_triad` package.

The test catalog, documentation excerpts, and AI Studio release metadata are static historical reference material. They are not live test results or a source of current package status. Run the Python test suite from the repository root to verify the engine.

Run the prototype from this directory:

```bash
bun install --frozen-lockfile
bun run dev
```

Validate the frontend:

```bash
bun run lint
bun run build
```

The archived release ZIP under `public/` is an original snapshot and does not include subsequent cleanup or fixes made to the Python project.
