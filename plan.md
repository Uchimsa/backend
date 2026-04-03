## Plan: Backend for CU Study App

Build a FastAPI + Supabase backend that serves content catalog (subjects/weeks/questions), generates and persists study stacks, tracks per-question progress, and exposes stats; keep schema minimal and endpoints clean, with Supabase Auth JWT validation and admin-only content management.

**Steps**

1. Define Supabase schema and enums for content and progress, matching the simplified single questions table with `type` plus optional fields, and add study-plan tables to persist stacks (_blocks step 2_).
2. Add Supabase configuration to settings, include URL/anon/service keys and JWT settings, and decide on an async access pattern (native async client if available; otherwise wrap sync calls via `asyncio.to_thread`) (_depends on 1_).
3. Create a thin data-access layer in `app/services/` for subjects, weeks, questions, study plans, progress, and sessions, with explicit user scoping and admin checks (_depends on 2_).
4. Add auth dependencies to validate Supabase JWTs, extract `user_id`, and enforce role checks for admin endpoints (_parallel with step 3_).
5. Implement API routes under `/api/v1` for:
   - Catalog: list subjects, list weeks by subject, list questions by week and type
   - User setup: attach/detach subjects for a user
   - Study plan: create plan from selected weeks + types + count; get next item; submit answer; end session and return stats
   - Stats: per-week/subject accuracy summary, recent sessions
   - Admin: CRUD for subjects, weeks, questions (_depends on 3 and 4_)
6. Add minimal validation and response models for tasks/tests/cards, with a single response shape that switches on `type` and keeps optional fields (`options`, `correct_option_index`, `answer_text`) (_parallel with step 5_).
7. Add placeholder schema and endpoints for `task_scans` without AI execution (create record, upload URL, read history) (_depends on 1, 5_).
8. Document API usage and example flows in README, including stack creation and answer submission payloads (_after steps 5-7_).

**Relevant files**

- [app/app.py](app/app.py) - app factory; include additional routers
- [app/router.py](app/router.py) - API root router; attach resource routers
- [app/core/settings.py](app/core/settings.py) - add Supabase config
- [app/api/**init**.py](app/api/__init__.py) - module entry for API routers
- [app/services/**init**.py](app/services/__init__.py) - service layer namespace
- [pyproject.toml](pyproject.toml) - add Supabase client dependency
- [README.md](README.md) - document endpoints and payloads

**Verification**

1. Run app locally and call: list subjects, create study plan, get next item, submit answers, end session.
2. Confirm that users can only access their own progress and sessions; admin endpoints require admin role.
3. Validate stats endpoints return correct per-week/subject aggregates.
4. Ensure tests and tasks return only relevant fields for the `type` and that optional fields are `null` when not applicable.

**Decisions**

- Keep a single `questions` table with `type` enum and optional columns for simplicity.
- Store study stacks server-side in a dedicated plan + items table so "next item" is consistent across devices.
- Use Supabase Auth JWT validation in FastAPI; apply admin checks for content management.
- Defer AI/OCR scoring; only persist uploads and metadata now.

**Further Considerations**

1. Admin role modeling: use Supabase `role` claim vs a separate `is_admin` flag in `users`.
2. RLS policy depth: minimal RLS plus backend checks vs strict RLS with service-role bypass.
3. Stack ordering: deterministic (by question id) vs randomized with a stored seed for reproducibility.
