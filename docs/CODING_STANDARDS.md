# Coding Standards

## General Principles
- Write self-documenting code. Minimize comments — use them only to explain "why," not "what."
- Prefer small, focused functions with a single responsibility.
- All public interfaces must have type annotations (TypeScript) or type hints (Python).
- No hardcoded secrets, API keys, or credentials. Use environment variables backed by GCP Secret Manager.
- All errors must be handled explicitly — no silent catches.

## TypeScript (Frontend + Orchestrator)

### Tooling
- Formatter: Prettier
- Linter: ESLint with `@typescript-eslint` plugin
- Package manager: npm
- Node version: 20 LTS

### Conventions
- Use `const` by default. Use `let` only when reassignment is necessary. Never use `var`.
- Use `interface` for object shapes, `type` for unions and intersections.
- Use `async/await` over raw Promises.
- Use named exports. Avoid default exports except for Next.js pages/layouts.
- File naming: `kebab-case.ts` for modules, `PascalCase.tsx` for React components.
- Use strict TypeScript (`"strict": true` in tsconfig).

### NestJS-Specific
- One module per feature/domain.
- Use dependency injection for all service dependencies.
- Use DTOs with `class-validator` decorators for request validation.
- Use interceptors for cross-cutting concerns (logging, error transformation).

### Next.js-Specific
- Use the App Router.
- Server Components by default. Add `"use client"` only when client interactivity is required.
- Colocate component styles with Tailwind utility classes.
- Use `EventSource` API for SSE subscriptions in client components.

## Python (Inference Service + Ingestion)

### Tooling
- Formatter: Ruff (format)
- Linter: Ruff (lint)
- Type checker: mypy (strict mode)
- Package manager: pip with `requirements.txt` per service
- Python version: 3.12

### Conventions
- Type hints on all function signatures and return types.
- Use `dataclasses` or Pydantic `BaseModel` for structured data.
- Use `pathlib.Path` over `os.path`.
- Use f-strings for string formatting.
- File naming: `snake_case.py`.
- Imports: standard library → third-party → local, separated by blank lines.

### FastAPI-Specific
- Use Pydantic models for all request/response schemas.
- Use dependency injection for shared resources (model loading, GCS client).
- Use `lifespan` context manager for startup/shutdown (model loading).
- Return explicit HTTP status codes.

## Error Handling

### TypeScript
```typescript
// Wrap external calls with typed error handling
try {
  const result = await inferenceService.predict(gameState);
  return result;
} catch (error) {
  logger.error("Inference call failed", { gameState, error });
  throw new InternalServerErrorException("Prediction unavailable");
}
```

### Python
```python
# Use specific exception types
try:
    prediction = model.predict(features)
except ValueError as e:
    logger.error("Invalid features for prediction", extra={"error": str(e)})
    raise HTTPException(status_code=422, detail="Invalid game state")
```

## Logging
- Use structured JSON logging in all services.
- Log levels: `error` for failures, `warn` for degraded states, `info` for request lifecycle, `debug` for development only.
- Never log sensitive data (API keys, raw user input beyond game state).
- Include correlation IDs (game ID, at-bat ID) in all log entries.
