# Specs

One folder per spec: `specs/<ID>-<slug>/` with `spec.md`, `security.md`, `test-cases.md` and `gate.md`.
The ID is the tracker issue or ticket key. Create packages with the `spec-create` skill or
`python sdd/tools/sdd.py spec new <ID> "<Title>"`; never by hand from memory.

The workflow is in [sdd/workflow.md](../sdd/workflow.md). Validate with
`python sdd/tools/sdd.py spec validate --all`.
