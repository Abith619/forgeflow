# Inventory app — design notes

Written 18 Sep 2026, covering apps/inventory (migrations 0001–0007) and the
`Company.code` fix in apps/accounts. This records the *reasoning* behind the
decisions, not the code — the code is in the repo, the "why" isn't.

---

## 1. StockQuant vs StockMove

| | what it is | lifecycle |
|---|---|---|
| `StockQuant` | current balance per (company, product, location) | overwritten constantly |
| `StockMove` | immutable record of one transfer: product, from, to, qty, user, reference, notes | append-only |

**Why both.** A quant table is current-state only, so it is overwritten and the
history is gone. Without moves you cannot answer "who moved 50 bolts out of
WH1/Stock on Tuesday, and why". Moves also make stock *reconcilable*: the sum of
moves in and out of a location must equal the quant. If it doesn't, there's a bug —
without moves you'd never know.

Same split as Odoo's `stock.quant` / `stock.move`.

---

## 2. Invariants live in the service layer, not `save()`

**Decision:** all quant writes go through `apps/inventory/services.py`.
Never write quants from a view, a serializer, or the admin.

**Why not `clean()` alone.** `clean()` is not called by `save()`, by
`objects.create()`, or by DRF's `ModelSerializer` (which runs its own validation
then calls `.save()` directly). It only protects Django admin and ModelForms.
Verified in the shell: `StockQuant.objects.create(...)` with a mismatched company
succeeded, `clean()` never ran.

**Why not override `save()`.** Costs a query per write (it must fetch
`self.location`), and `bulk_create()` bypasses `save()` by design anyway — so the
guarantee still has a hole.

**Why not a DB trigger.** Bulletproof, but heavy and awkward to express in Django
migrations.

A service function is also the only place with a view of *both* sides of a move —
a method on `StockQuant` can only see one row.

---

## 3. Locking in `move_stock`

One query, evaluated, ordered:

```python
list(StockQuant.objects.select_for_update()
     .filter(company=company, product=product,
             location__in=[from_location, to_location])
     .order_by("location_id"))
```

then keyed into a dict by `location_id` so source and destination are named
variables, not list positions.

**Why `list()`.** Querysets are lazy. An unevaluated `select_for_update()` builds
a query object and sends *nothing* to Postgres — no `SELECT ... FOR UPDATE`, no
lock. The lock exists only once something consumes the queryset, and holds only
for the remainder of that transaction.

**Why one query with `order_by`, not two `.get()` calls.** Postgres acquires row
locks in the order rows are returned. Ordering by `location_id` means *every*
caller locks the lower id first, whichever direction it is moving. Two separate
`select_for_update().get()` calls in source-then-destination order would give
inconsistent ordering, and A→B racing B→A would deadlock.

**Why plain `-=` / `+=` and not `F()`.** The rows are already locked, so the reads
are current and nobody can write underneath us. `F()` is the *alternative* to
locking, not a supplement — and it can't make a decision, which the sufficiency
check requires.

### Lost update — the bug this prevents

`self.quantity += qty; self.save()` does the arithmetic in Python on a possibly
stale value. Two concurrent receipts of 10 against a quant at 100:

| | A | B | DB |
|---|---|---|---|
| t1 | reads 100 | | 100 |
| t2 | | reads 100 | 100 |
| t3 | writes 110 | | 110 |
| t4 | | writes 110 | **110** |

Twenty units arrived, the database says ten, and nothing errored. This is the most
common source of "our stock numbers are wrong and nobody knows why".

---

## 4. The destination quant

```python
if not destination:
    destination, _ = StockQuant.objects.get_or_create(...)
    destination = StockQuant.objects.select_for_update().get(pk=destination.pk)
```

**Why the re-fetch.** `SELECT ... FOR UPDATE` locks *rows*. A row that doesn't
exist can't be locked, so the main lock query can't cover a destination that isn't
there yet. And `get_or_create`'s internal `get()` calls run on the **plain**
manager — confirmed by reading `django/db/models/query.py` — so whatever it
returns is unlocked. Without the re-lock, two movers into a fresh location can
both `+=` from the same stale read: the lost update again, at the one row the
ordered query couldn't reach.

**No outer nested `atomic()` needed.** `get_or_create` already wraps its insert in
its own savepoint, catches `IntegrityError`, and re-fetches the winner's row. The
unique constraint on (company, product, location) is what makes that recovery
safe.

**Is the late lock a deadlock risk?** No, conditionally. For another transaction
to hold that row it must either (a) have created it and not committed — in which
case the row is invisible to us under READ COMMITTED and we block on the unique
constraint, while that transaction waits on nothing of ours; or (b) hold it as its
own source — in which case it existed and was committed before, so our ordered
query would have returned it and we'd never be in this branch. Both are
contradictions.

**This proof depends on two things.** Postgres READ COMMITTED (the default), and
`move_stock` locking exactly two quant rows and nothing else. **Redo the analysis**
before adding reservations, multi-source moves, or any second table locked inside
this transaction.

---

## 5. Deadlock retry

```python
for attempt in range(MAX_MOVE_RETRIES):
    try:
        with transaction.atomic():
            ...
            return ...
    except OperationalError as e:
        if not isinstance(e.__cause__, DeadlockDetected):
            raise
        if attempt == MAX_MOVE_RETRIES - 1:
            raise
```

**Why `try` outside the `with`.** A deadlock aborts the entire transaction. Django
flags the connection `needs_rollback` and any further query raises
`TransactionManagementError`. Retrying an *inner* block is impossible by
construction — there is nothing left to retry into. The retry must unwind out of
`atomic()` and open a fresh transaction.

**Why only deadlocks.** Retrying is safe here precisely because the failed attempt
committed nothing. A statement timeout or dropped connection is not the same
situation, so anything that isn't a `DeadlockDetected` cause escapes immediately.

**Why not `ValidationError`.** `ValidationError` means the caller sent something
invalid → DRF renders a 400. A deadlock is not the caller's fault. Let the
`OperationalError` propagate as a 500, which is what it is.

**Why every path ends in `return` or `raise`.** A loop that falls off its end
returns `None`, and `mv, src, dst = move_stock(...)` then fails with an unrelated
`TypeError` that hides the real cause — or worse, a caller ignoring the return
value treats total failure as success.

**This cannot be unit-tested easily** — provoking a real deadlock needs two
concurrent connections fighting over rows in opposite order. Reading the control
flow *is* the test, which is the other reason every branch must terminate
explicitly.

---

## 6. Where each invariant lives, and why

| invariant | enforced by | raises |
|---|---|---|
| unique (company, product, location) | DB `UniqueConstraint` | `IntegrityError` |
| `quantity >= 0` | DB `CheckConstraint` `quantity_non_negative` | `IntegrityError` |
| `reserved_qty >= 0` | DB `CheckConstraint` `reserved_qty_non_negative` | `IntegrityError` |
| `quantity >= reserved_qty` | DB `CheckConstraint` `reserved_qty_lte_quantity` | `IntegrityError` |
| `code != ''` on Company | DB `CheckConstraint` `company_code_not_empty` | `IntegrityError` |
| quant.company == location.company | `clean()` + service | `ValidationError` |
| sufficient stock to move | service | `ValidationError` |

**Why the split.** A SQL `CHECK` is evaluated on one row and cannot join. The three
quant checks compare columns of the same table, so the database can express them.
The company/location match spans two tables, so it can only live in Python. That
distinction is the whole reason this model has two enforcement mechanisms.

**Why both layers.** Constraints make bad data impossible on *every* path —
including `psql`, a bulk update, or a data migration. Application checks give the
user a readable 400 before a constraint fires an unhandled 500. Neither replaces
the other.

**Why one rule per constraint, never combined with `&`.** The error names which
invariant broke. Combined, all three violations report the same constraint name and
you're guessing. Verified: three different bad writes produced three different
constraint names.

**Naming matters.** A constraint called `reserved_qty_lte_quantity` that actually
checks `quantity >= 0` is worse than no name — the next person reads the name and
looks in the wrong place. (This happened during the build.)

---

## 7. Decisions taken

- **`quantity` may NOT go negative.** Chose the strict rule over Odoo's
  "negative = stock owed". The service's sufficiency check is the friendly path in
  front of the constraint. Consequence: any code driving a quant negative outside
  the service gets an `IntegrityError` 500, by design.
- **`StockMove.user` is required** (non-null, `PROTECT`). Every move records who
  did it. **Consequence: a system user account is needed** — `is_active=False`,
  seeded by a data migration — before any SAP import, scheduled job or data
  migration can move stock. Retrofitting means backfilling orphaned moves.
- **`reference` stays a plain `CharField`** for now. Deliberate: a FK to a source
  document (generic, so one field can point at a PO, SO or adjustment) is the real
  shape, but deferred. Today a typo is undetectable and "show me every move against
  this PO" isn't answerable.
- **`settings.AUTH_USER_MODEL`, never `"accounts.User"`.** Hardcoding breaks if the
  user model moves or is swapped.
- **`related_name` is named for what the reverse query returns, from the target's
  point of view** — `product.stock_moves`, `location.outgoing_moves` /
  `incoming_moves`. Not `related_name="product"`, which yields the nonsense
  `product.product`.

---

## 8. Migrations — lessons paid for

**`makemigrations` never looks at the database.** It compares model state to
migration state. The "impossible to add a non-nullable field" prompt appears
regardless of whether the table has rows.

**Adding a constraint to a live table is two jobs**, and order matters:

1. deploy code that stops writing bad data
2. run a data migration that fixes rows already there
3. *then* add the constraint

Done out of order, `migrate` aborts with `CheckViolation ... violated by some row`.
Cost here was one error message on a 3-row table; on 3M rows with customers it's an
outage in the deploy window.

**Adding a non-nullable FK to a table with rows** — the production sequence is
three migrations: add as `null=True`, data-migrate to backfill, alter to non-null.
Never accept the interactive one-off default on a populated table: it bakes a
fabricated value into migration history and, for a `user` column, falsifies the
audit trail. On an *empty* table a one-off default with
`preserve_default=False` is harmless — it fills nothing and isn't kept on the field.

**Postgres has transactional DDL** and Django wraps each migration in a
transaction, so a failed migration rolls back whole — you are never half-migrated.
MySQL would leave a mess requiring manual repair. One concrete reason to run
Postgres.

**A `CharField` you don't set is `""`, not `NULL`.** Django's `Field.get_default()`
returns the empty string for non-nullable string fields with no explicit default.
Postgres treats `""` as a real value, so `unique=True` permits exactly one such row
and rejects every one after with a confusing duplicate-key error about a value
nobody typed. Hence `company_code_not_empty`: fail on the actual mistake, not on
its consequence two rows later.

---

## 9. Testing notes

- **The Django admin cannot exercise the service.** Admin only calls
  `Model.save()`, so adding a `StockMove` through it writes a move row and moves no
  stock. Test from `manage.py shell`; register quants/moves read-only in the admin
  for *inspection* only.
- **On shell restart, Python variables are gone but every database row persists.**
  Re-`import` and re-`get()` — never re-`create()`.
- **`manage.py check` doesn't touch the database.** It validates model state only.
  `sqlmigrate` only *prints* SQL; it executes nothing. Model says it / migration
  exists / database enforces it are three separate claims.
- The three cases every stock-move change should be re-verified against:
  destination exists, destination missing (created and credited), insufficient
  stock (raises **and** leaves both balances and `StockMove.objects.count()`
  untouched — that last one is the proof `atomic()` works).

---

## 10. Open

- DRF endpoint over `move_stock` — not built.
- System user data migration — not built, blocks all automated callers.
- `reference` as a real document FK — deferred by decision.
- `Company.name` has no non-empty constraint (`~Q(name="")` would mirror the code
  one).
- `retry` pip package was installed then abandoned in favour of the hand-written
  loop — uninstall and remove from `requirements/base.txt` if still listed.

---

## 11. The API layer (added 18 Sep 2026)

`POST /api/inventory/moves/` — `apps/inventory/{serializers,views,urls}.py`.
DRF + djangorestframework-simplejwt.

**Auth is one setting.** `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` is an
ordered list tried until one identifies the request; swapping Session → Token →
JWT is a change to that list and nothing else. Both JWT and Session are enabled:
JWT for API clients, Session so the browsable API and admin keep working in dev.

**`DEFAULT_PERMISSION_CLASSES` is set explicitly to `IsAuthenticated`.**
Why: DRF's own default is `AllowAny`. Unset, every new view is public until
someone remembers to lock it. Defaulting closed and opening the few public
endpoints is the safe direction.

### The rule: `user` and `company` never come from the request body

The request serializer declares only `product`, `from_location`, `to_location`,
`quantity`, `reference`, `notes`. The view supplies `user=request.user` and
`company=request.user.company`.

Why: accepting `user` would let any authenticated client attribute a move to
anyone, defeating the non-null `StockMove.user` entirely. Accepting `company`
would let an Acme user move Globex stock by sending `company: 5` — a cross-tenant
breach, and the most common bug in multi-tenant SaaS.

This is enforced structurally, not by convention: because the view passes
`**validated_data` *plus* explicit `user=`/`company=`, a serializer that leaked
either field would raise `TypeError: got multiple values for keyword argument`
and 500. A 201 is therefore proof both were dropped.

### Tenant scoping lives in the serializer's querysets

`PrimaryKeyRelatedField` resolves an id via `queryset.get(pk=value)`. Scope the
queryset to the caller's company and a foreign id simply isn't found — DRF
returns a clean 400 keyed to that field. Tenant isolation as a side effect of
field resolution, with no separate validation to forget.

Mechanics that matter:
- Class-level querysets are `.objects.none()` placeholders — **fail closed**. If
  per-request scoping ever fails to run, every id is rejected rather than every id
  accepted.
- Scoping happens in `__init__` **after** `super().__init__()`, assigning to
  `self.fields["x"].queryset` — the instantiated field objects. Mutating the
  *class* attribute would leak one request's scope into every other request
  process-wide. This is the line-ordering detail that becomes a cross-tenant leak
  under load.
- `self.context.get("request")` with an early return, not `self.context["request"]`
  — a serializer built without context (tests, shell, browsable API form) would
  otherwise KeyError.

### Plain `Serializer` on the write path, `ModelSerializer` on the read path

The request serializer is a plain `Serializer` with no `create()`. A
`ModelSerializer` here would inherit a `create()` that writes the StockMove row
directly and bypasses `move_stock` — the false-receipt problem again. On the
response side `ModelSerializer` is fine: there is nothing to bypass when reading.
Its `fields` are listed explicitly, never `"__all__"` — with `__all__`, adding a
model column silently publishes it through the API.

### Exception mapping — Django's ValidationError is not DRF's

`django.core.exceptions.ValidationError` and
`rest_framework.exceptions.ValidationError` are different classes, and DRF
auto-converts only its own. The service raises Django's, so the view must catch
and re-raise:

```python
except DjangoValidationError as e:
    raise DRFValidationError(e.message_dict if hasattr(e, "message_dict") else e.messages)
```

Without this, "Insufficient stock" — an ordinary user error — returns 500.
The `hasattr` branch is needed because the service raises both shapes: a bare
string (`.messages` only) and a dict from `clean()` (`.message_dict`).
Import both classes under aliases; two same-named classes with different
behaviour in one file is exactly where a silent 500 comes from.

### Other notes

- A bare `APIView` does **not** populate serializer context — pass
  `context={"request": request}` explicitly. DRF's *generic* views do it via
  `get_serializer_context()`. Omit it and every id 400s as "does not exist",
  which looks like bad data rather than missing wiring.
- A bare `APIView` also has no `get_serializer()`, so the browsable API renders a
  raw JSON textarea instead of an HTML form. Not a bug.
- Returns `201 Created`, not 200.
- `reference`/`notes` are `required=False` with **no** serializer default, so an
  omitted field is absent from `validated_data` and the service's own `''`
  defaults apply — one source of truth for the default instead of two.

### Verified end to end (18 Sep 2026)

| test | result |
|---|---|
| valid payload | 201, move created, `user` from request |
| quantity 99999 | 400 `["Insufficient stock"]` — not 500 |
| `from_location` = another tenant's id | 400 `Invalid pk "5" - object does not exist.` at the serializer |
| `user`/`company` injected into payload | 201, both silently dropped |

### Accounts fixes made along the way

- `User.company` was `null=True` in migration 0001 while the model said
  `null=False` — **model/DB drift**, undetectable by `manage.py check`. Use
  `makemigrations --check --dry-run` (good CI gate). Fixed in accounts/0004.
- Root cause of the NULL: `REQUIRED_FIELDS = []`, so `createsuperuser` never
  prompted for `company` (or `full_name`). Still to fix — either add `company` to
  `REQUIRED_FIELDS` (FKs there are awkward: createsuperuser cleans input to a raw
  pk and assigning an int to a FK attribute raises ValueError — test it) or guard
  it in `UserManager.create_user` alongside the existing email check.
- simplejwt returns the same "No active account found with the given credentials"
  for wrong password, unknown email and inactive account — deliberate, so the error
  can't be used to enumerate registered emails.

### Still open

- System user data migration (`is_active=False`) — blocks automated callers.
- `REQUIRED_FIELDS` / `create_user` guard for `company`.
- No GET/list endpoint for moves or quants yet.
- `Company.name` has no non-empty constraint.
- `retry` pip package installed then abandoned — remove from requirements if listed.
