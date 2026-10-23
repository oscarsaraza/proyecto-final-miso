# Critical paths

A change that touches one of these paths needs a spec package that declares it under "Affected paths",
with the critical paths trigger set to YES and at least the minimum profile listed. In merge requests,
`python sdd/tools/sdd.py scan paths --base <base>` fails when a critical file changed and no
spec package changed in the same branch declares it. This applies to every branch, hotfixes included.
The only waiver is `SPEC-EXEMPT: <reason>` in a commit message, for a change that cannot have a package
(such as installing this framework), accepted by a person and visible in the history.

Changing this file is itself a critical change: it is reviewed like code.

## Default critical paths

Generic patterns that hold for most stacks. Keep them unless a pattern clearly does not apply.

| Pattern | Area | Why | Minimum profile |
|---|---|---|---|
| **/auth/** | Authentication | Credentials, sessions and tokens | HIGH |
| **/authn/** | Authentication | Credentials, sessions and tokens | HIGH |
| **/authz/** | Authorization | Permissions and ownership checks | HIGH |
| **/identity/** | Identity | Accounts, credentials and identity proofing | HIGH |
| **/oauth/** | Authentication | Delegated authorization | HIGH |
| **/crypto/** | Cryptography | Keys, hashing and encryption | HIGH |
| **/payments/** | Payments | Money movement | HIGH |
| **/billing/** | Payments | Money movement | HIGH |
| **/migrations/** | Data | Schema and data changes, including personal data | HIGH |
| **/*.tf | Infrastructure | Network, IAM, encryption, secrets | HIGH |
| **/k8s/** | Infrastructure | Workload exposure and secrets | HIGH |
| **/helm/** | Infrastructure | Workload exposure and secrets | HIGH |
| **/Dockerfile* | Infrastructure | Base images and runtime user | HIGH |
| **/docker-compose*.yml | Infrastructure | Exposed ports and credentials | MEDIUM |
| .github/workflows/** | Pipeline | Credentials, permissions and gates | HIGH |
| .gitlab-ci.yml | Pipeline | Credentials, permissions and gates | HIGH |
| **/.env.example | Configuration | Expected secrets and defaults | MEDIUM |
| **/AndroidManifest.xml | Mobile | Backups, exported components, network config | HIGH |
| **/network_security_config.xml | Mobile | Cleartext and certificate trust | HIGH |
| **/Info.plist | Mobile | Transport security and permissions | HIGH |
| **/*.entitlements | Mobile | Platform capabilities | HIGH |
| sdd/hooks/** | Framework | The gates themselves | HIGH |
| sdd/tools/sddlib/** | Framework | The validator and scanners | HIGH |
| sdd/config.json | Framework | Protected branches and spec-first scope | HIGH |
| sdd/security/critical-paths.md | Framework | This registry | HIGH |
| **/package.json | Dependencies | Supply chain | MEDIUM |
| **/pyproject.toml | Dependencies | Supply chain | MEDIUM |
| **/requirements*.txt | Dependencies | Supply chain | MEDIUM |
| **/*.gradle* | Dependencies | Supply chain and build configuration | MEDIUM |
| **/libs.versions.toml | Dependencies | Supply chain | MEDIUM |
| **/go.mod | Dependencies | Supply chain | MEDIUM |
| **/pom.xml | Dependencies | Supply chain | MEDIUM |

## Project critical paths

Add this repository's own critical paths: security configuration, session storage, public API routers,
seed data, deployment scripts. Keep the patterns precise; an over-broad pattern trains people to waive it.

| Pattern | Area | Why | Minimum profile |
|---|---|---|---|
