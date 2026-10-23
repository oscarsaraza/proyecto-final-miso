---
name: secure-coding-python
description: Secure coding patterns for Python and FastAPI — per-resource authorization, bounded input, safe queries, error handling, configuration without default secrets, password and token handling, one-time codes, client IP behind proxies, CORS, rate limits, outbound calls and logging. Use when writing or reviewing Python that handles requests, data, credentials or configuration.
---

# Secure coding — Python and FastAPI

Each pattern names the weakness it prevents (CWE) and the test that proves it. The control catalog is
`sdd/security/controls.md`; algorithms and key rules are in `sdd/rules/cryptography.md`.

## Authorization per resource (CWE-639, CWE-862)

The owner or tenant comes from the verified token and is part of every query for scoped data. A
resource that exists but belongs to someone else answers exactly like one that does not exist.

```python
async def get_policy(session: AsyncSession, holder_id: str, policy_id: int) -> PolicyDB:
    policy = await session.scalar(
        select(PolicyDB).where(PolicyDB.id == policy_id, PolicyDB.holder_id == holder_id)
    )
    if policy is None:
        raise PolicyNotFoundError()
    return policy
```

Never: load by ID and compare afterwards in some routes only; take the owner, tenant or partner from a
header, query parameter or body. Test: another user's identifier returns 404 and no data.

## Bounded input (CWE-20, CWE-770)

```python
class BeneficiaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=120)
    document_number: str = Field(pattern=r"^\d{5,12}$")
    share: Decimal = Field(gt=0, le=100, max_digits=5, decimal_places=2)


class PolicyIssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beneficiaries: list[BeneficiaryRequest] = Field(min_length=1, max_length=5)
```

Never: `dict`, `Any` or unbounded `str` and `list` in request models. Test: over-long, wrong-typed and
extra fields return 422 before touching the database.

## Queries (CWE-89)

SQLAlchemy expressions, or `text()` with bound parameters. Never build SQL with f-strings, `%` or `+`,
including `ORDER BY` columns: map them from an allow-list.

## Errors (CWE-209, CWE-532)

```python
@app.exception_handler(DomainError)
async def domain_error(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.public_message})
```

Never `detail=str(exc)`; unexpected exceptions become a generic 500 and are logged with a correlation ID,
without the request body. Test: a forced internal error returns a body with no stack trace or SQL.

## Configuration (CWE-798, CWE-1188)

```python
class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "test", "staging", "production"]
    JWT_SECRET_KEY: SecretStr
    CORS_ORIGINS: list[str] = []
    TRUSTED_PROXIES: list[str] = []


DEVELOPMENT = settings.ENVIRONMENT == "development"
```

- Secrets have no default: the app does not start without them.
- Debug features (seed accounts, codes in responses, documentation endpoints) are on only when the
  environment is explicitly development — never `!= "production"`, which turns them on when the variable is missing.

```python
app = FastAPI(
    docs_url="/docs" if DEVELOPMENT else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DEVELOPMENT else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
```

Never `allow_origins=["*"]` with credentials. Test: with `ENVIRONMENT` unset the app refuses to start;
in production `/docs` returns 404.

## Passwords (CWE-916, CWE-521)

- Argon2id for new hashes (`argon2-cffi`, after `dependency-review`); existing bcrypt hashes are verified
  and rehashed on the next successful login. bcrypt truncates at 72 bytes: reject longer passwords.
- Hashing is CPU-bound: `await asyncio.to_thread(hasher.hash, password)`.
- Length rules and a blocklist, not composition rules (NIST SP 800-63B Rev. 4).

## Tokens (CWE-347, CWE-613)

```python
claims = jwt.decode(
    token,
    settings.JWT_SECRET_KEY.get_secret_value(),
    algorithms=["HS256"],
    options={"require": ["exp", "iat", "sub"]},
)
```

- The algorithm list is fixed; never read it from the token header.
- Access and refresh tokens are distinguished by a claim and rejected in the wrong place.
- Revocation (logout, password change) is checked on every request to sensitive routes — a token
  version or a denylist — not only at refresh.
- One key per purpose: the token signing key is not reused for one-time codes or other MACs.

## One-time codes and random values (CWE-330, CWE-640)

```python
code = f"{secrets.randbelow(1_000_000):06d}"
digest = hmac.new(otp_key, code.encode(), hashlib.sha256).hexdigest()
valid = hmac.compare_digest(digest, stored_digest)
```

Single use, short expiry, limited attempts, stored as a keyed MAC with a dedicated key. Never `random`
for security values; never return the code in a response outside local development.

## Client IP behind proxies (CWE-348)

```python
def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else ""
    if peer not in settings.TRUSTED_PROXIES:
        return peer
    hops = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
    for hop in reversed(hops):
        if hop not in settings.TRUSTED_PROXIES:
            return hop
    return peer
```

Never the first `X-Forwarded-For` value or a CDN header without checking that the request came through
that CDN. Test: a forged header from an untrusted peer does not change the rate-limit key.

## Rate limits and lockout (CWE-307)

Counters in shared storage (database or cache), keyed per account and per trusted client IP, with
progressive delays. Responses do not reveal whether the account exists (CWE-204): same message, same
status and similar timing.

## Outbound calls (CWE-918, CWE-400)

Fixed hosts from configuration, never a URL from the client. Explicit timeouts, bounded retries with
backoff, and the response validated with a model before use. Credentials from the secrets manager.

## Other sinks

- Deserialization: no `pickle` or `yaml.load` on untrusted data; `yaml.safe_load`, `json` (CWE-502).
- Commands: `subprocess.run([...])` with a list and `shell=False`; never user input in a shell string (CWE-78).
- Files: size and type limits, generated names, never a path from the client (CWE-22, CWE-434).

## Logging (CWE-532)

Log the event, the user ID and a correlation ID. Never passwords, codes, tokens, secrets, document
numbers, emails or request bodies.

## Review checklist

- [ ] Scoped queries filter by the owner or tenant from the token; out-of-scope answers 404.
- [ ] Request models bounded and closed; no `dict` or `Any`.
- [ ] No string-built SQL; no `str(exc)` to clients.
- [ ] No default secrets; debug features only when the environment is explicitly development.
- [ ] CORS restricted; documentation endpoints off outside development.
- [ ] Tokens with fixed algorithms, required claims and revocation; one key per purpose.
- [ ] Codes from `secrets`, stored as MACs, compared in constant time.
- [ ] Client IP only through trusted proxies; rate limits in shared storage.
- [ ] Outbound calls to fixed hosts with timeouts; no unsafe deserialization or shell.
- [ ] Logs without personal data or secrets.
