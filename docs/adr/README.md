# Architecture decision records

One file per decision, numbered in order and never renumbered. The template is
[`sdd/templates/adr.md`](../../sdd/templates/adr.md) and the procedure is the `adr` skill. All of these
are **Proposed**: they describe the architecture the code has today and the rules for new code, and the
team accepts or changes them.

## System

| ADR | Decision |
|---|---|
| [0001](0001-system-separated-applications.md) | Separated applications that talk only through the backend API |
| [0002](0002-api-contract.md) | API contract between the backend and its clients |

## Backend (FastAPI)

| ADR | Decision |
|---|---|
| [0003](0003-backend-hexagonal-architecture.md) | Hexagonal architecture (ports and adapters) per domain module |
| [0004](0004-backend-module-layout.md) | Fixed file layout per module |
| [0005](0005-backend-bff-per-channel.md) | One BFF router per client channel as driving adapters |
| [0006](0006-backend-persistence.md) | Persistence with async SQLAlchemy behind repository ports |
| [0007](0007-backend-errors-and-responses.md) | Domain errors and HTTP error responses |

## Web portal (Angular)

| ADR | Decision |
|---|---|
| [0008](0008-web-components-and-signals.md) | Standalone components, signals and zoneless change detection |
| [0009](0009-web-feature-structure.md) | Feature-based structure with a container per flow |
| [0010](0010-web-http-and-session.md) | HTTP through core services, one interceptor, session in `core/auth` |
| [0011](0011-web-forms.md) | Template-driven forms bound to signals |
| [0012](0012-web-styles-and-design-tokens.md) | Styles with design tokens and no component library |

## Mobile app (Android)

| ADR | Decision |
|---|---|
| [0013](0013-mobile-mvvm-layers.md) | MVVM with domain, data and ui layers per feature |
| [0014](0014-mobile-dependency-injection.md) | Manual dependency injection in the Application class |
| [0015](0015-mobile-navigation.md) | Screen switching by UI state in one activity |
| [0016](0016-mobile-networking.md) | HTTP with `HttpURLConnection` behind domain interfaces |
| [0017](0017-mobile-credential-storage.md) | Credentials protected by the Keystore and biometrics; tokens only in memory |
| [0021](0021-mobile-encrypted-local-database.md) | An encrypted local database per account with Room and SQLCipher |

## Infrastructure (Terraform)

| ADR | Decision |
|---|---|
| [0018](0018-terraform-root-and-modules.md) | One Terraform root composing a local module per AWS component |
| [0019](0019-terraform-environments-and-state.md) | Environments and Terraform state |
| [0020](0020-private-load-balancer-behind-cloudfront.md) | A private load balancer that only CloudFront reaches |

## How we write them

- **One decision per ADR**, readable in about five minutes, with the template's sections in order:
  context, options considered, decision, consequences, security and privacy impact.
- **Adapted to each application.** Each layer records its own architecture; a rule from one does not
  carry over to another unless an ADR says so.
- **Structure decisions fix the layout**: the folders and files and what goes in each, so new code lands
  in a known place instead of new files and layers each time. Code reviews check against the accepted
  ADRs (`code-review-<language>`).
- **Describe what exists before changing it**, citing paths. A decision that changes direction says what
  migrates, and whether at once or when the code is next touched. Known gaps are listed and fixed in
  their own story or hotfix, not inside the ADR.
- **Status:** Proposed → Accepted (by the team, with names and date) → Superseded by NNNN or Deprecated.
  An accepted decision is not edited; a new ADR supersedes it. Agents draft ADRs; they never accept them.
- **When:** a new layer, module or pattern; a dependency that shapes the code (frameworks, DI,
  navigation, state, HTTP clients); the topics of the ADR gate (base images, network, IAM, keys,
  authentication, AI SDKs).
