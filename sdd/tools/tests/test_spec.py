import unittest
from datetime import date

from base import TEMPLATES, Scenario


class ValidPackage(Scenario):
    def test_complete_package_is_verified(self):
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("HIGH", result.profile)
        self.assertEqual("SECURITY_VERIFIED", result.computed)

    def test_more_conservative_state_only_warns(self):
        self.declare("SECURITY_REVIEW_PENDING")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertIn("W09", {f.code for f in result.warnings})

    def test_risk_accepted_by_a_person(self):
        self.edit("security.md", "| LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |",
                  "| MEDIUM | MEDIUM | MEDIUM | ACCEPT | Medium: accepted until the redesign | ACCEPTED |")
        self.edit("gate.md", "| Risk | Decision | Approved by | Role | Date | Expires |\n|---|---|---|---|---|---|",
                  "| Risk | Decision | Approved by | Role | Date | Expires |\n|---|---|---|---|---|---|\n"
                  "| RISK-01 | Accept until the redesign | Ana Reviewer | Tech lead | 2026-10-20 | 2026-12-31 |")
        self.declare("RISK_ACCEPTED")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("RISK_ACCEPTED", result.computed)

    def test_done_with_full_closeout(self):
        self.edit("spec.md", "| Status | IN_REVIEW |", "| Status | DONE |")
        self.edit("gate.md", "| Criterion | Result | Evidence |\n|---|---|---|",
                  "| Criterion | Result | Evidence |\n|---|---|---|\n| AC-01 | MET | tests/test_policies.py::test_owner_lists_policies |\n"
                  "| AC-02 | MET | tests/test_policies.py::test_error_hides_personal_data |\n"
                  "| QR-01 | MET | Load test summary of 2026-10-20 |")
        self.assertNoErrors(self.validate())

    def test_done_needs_quality_requirements_in_closeout(self):
        self.edit("spec.md", "| Status | IN_REVIEW |", "| Status | DONE |")
        self.edit("gate.md", "| Criterion | Result | Evidence |\n|---|---|---|",
                  "| Criterion | Result | Evidence |\n|---|---|---|\n| AC-01 | MET | tests/test_policies.py::test_owner_lists_policies |")
        self.assertError(self.validate(), "E34", "QR-01")


class WithoutSignatures(Scenario):
    def setUp(self):
        super().setUp()
        (self.repo / "sdd" / "config.json").write_text('{"requireSignatures": false}', encoding="utf-8")

    def test_merge_request_approval_replaces_the_review_row(self):
        self.cut("gate.md", "| Ana Reviewer |", "## Risk acceptance")
        self.edit("gate.md", "## Security reviews\n", "## Security reviews\n\n| Reviewer | Role | Date | Scope | Result |\n|---|---|---|---|---|\n\n")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("SECURITY_VERIFIED", result.computed)

    def test_risk_decided_in_the_spec_needs_no_signature(self):
        self.edit("security.md", "| LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |",
                  "| MEDIUM | MEDIUM | MEDIUM | ACCEPT | Medium: accepted until the redesign | ACCEPTED |")
        self.declare("RISK_ACCEPTED")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("RISK_ACCEPTED", result.computed)

    def test_an_agent_still_cannot_sign(self):
        self.edit("gate.md", "| Ana Reviewer |", "| Claude |")
        self.assertError(self.validate(), "E26")


class WithSignatures(Scenario):
    def test_accepted_risk_without_signature_is_rejected(self):
        self.edit("security.md", "| LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |",
                  "| MEDIUM | MEDIUM | MEDIUM | ACCEPT | Medium: accepted until the redesign | ACCEPTED |")
        self.assertError(self.validate(), "E22", "RISK-01")


class LowProfile(Scenario):
    fixture = "valid_low"

    def test_trivial_change_needs_no_extensive_model(self):
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("LOW", result.profile)
        self.assertEqual("SECURITY_VERIFIED", result.computed)

    def test_low_cannot_skip_threats_with_authentication(self):
        self.edit("spec.md", "| Authentication, sessions, credentials or one-time codes | NO |",
                  "| Authentication, sessions, credentials or one-time codes | YES |")
        result = self.validate()
        self.assertError(result, "E24", "declared profile LOW")
        self.assertError(result, "E03", "Threat model")
        self.assertError(result, "E03", "Secrets and keys")
        self.assertError(result, "E03", "Authentication, authorization and sessions")


class FreshTemplate(Scenario):
    def test_new_package_from_templates_does_not_pass(self):
        for file in self.package.iterdir():
            file.unlink()
        for template in TEMPLATES.glob("*.md"):
            text = (template.read_text(encoding="utf-8").replace("{{ID}}", "HU-NEW").replace("{{TITLE}}", "New")
                    .replace("{{DATE}}", date.today().isoformat()).replace("{{SPEC_PATH}}", "specs/HU-NEW"))
            (self.package / template.name).write_text(text, encoding="utf-8")
        result = self.validate()
        self.assertGreater(len(result.errors), 20)
        self.assertNotEqual("SECURITY_VERIFIED", result.computed)
        self.assertTrue(any("profile" in f.message.lower() for f in result.errors))


class IncompleteSpec(Scenario):
    def test_missing_file(self):
        (self.package / "test-cases.md").unlink()
        self.assertError(self.validate(), "E01")

    def test_missing_section(self):
        self.edit("security.md", "## 7. Attack surface", "## 7. Something else")
        self.assertError(self.validate(), "E02", "Attack surface")

    def test_missing_design_section(self):
        self.edit("spec.md", "## 2. Design", "## 2. Notes")
        self.assertError(self.validate(), "E02", "2. Design")

    def test_reference_to_undefined_id(self):
        self.edit("spec.md", "| Another holder's resource answers 404 | CTL-02 |", "| Another holder's resource answers 404 | CTL-09 |")
        self.assertError(self.validate(), "E07", "CTL-09")

    def test_duplicate_id(self):
        self.edit("security.md", "| CTL-02 | Another holder's", "| CTL-01 | Another holder's")
        self.assertError(self.validate(), "E06", "CTL-01")

    def test_profile_below_triggers(self):
        self.edit("spec.md", "| Security profile | HIGH |", "| Security profile | MEDIUM |")
        self.assertError(self.validate(), "E24", "minimum HIGH")

    def test_threat_model_cannot_be_na_with_authorization(self):
        self.cut("security.md", "| ID | STRIDE |", "## 9.")
        self.edit("security.md", "## 8. Threat model\n", "## 8. Threat model\n\nN/A: not needed here.\n\n")
        self.assertError(self.validate(), "E03", "Threat model")

    def test_inventory_inconsistent_with_triggers(self):
        self.edit("spec.md", "| Personal data (identifies or can identify a person) | YES |",
                  "| Personal data (identifies or can identify a person) | NO |")
        self.assertError(self.validate(), "E24", "personal data")

    def test_invalid_spec_status(self):
        self.edit("spec.md", "| Status | IN_REVIEW |", "| Status | ALMOST |")
        self.assertError(self.validate(), "E27", "ALMOST")


class TraceabilityAndControls(Scenario):
    def test_acceptance_criterion_without_test_case(self):
        self.edit("test-cases.md", "| Covers | AC-01 |", "| Covers | SR-01 |")
        self.assertError(self.validate(), "E33", "AC-01")

    def test_control_without_tests(self):
        self.edit("security.md", "| THR-02 | TC-03 | T-02 |", "| THR-02 | — | T-02 |")
        self.assertError(self.validate(), "E10", "CTL-03")

    def test_not_applicable_control_without_rationale(self):
        self.edit("security.md", "| Single channel, no tenants exist |", "| — |")
        self.assertError(self.validate(), "E11", "CTL-05")

    def test_requirement_without_mitigation(self):
        self.edit("spec.md", "| DATA-01, THR-02 | CTL-03 |", "| DATA-01, THR-02 | CTL-05 |")
        self.assertError(self.validate(), "E08", "SR-02")

    def test_requirement_without_security_test(self):
        self.edit("test-cases.md", "| Covers | AC-02, SR-02 |", "| Covers | AC-02, SR-01 |")
        self.assertError(self.validate(), "E09", "SR-02")

    def test_missing_control_without_task(self):
        self.edit("security.md", "| CTL-04 | Token signature and expiry verified in the backend | API | EXISTING |",
                  "| CTL-04 | Token signature and expiry verified in the backend | API | MISSING |")
        self.assertError(self.validate(), "E12", "CTL-04")

    def test_missing_control_with_task_lowers_state(self):
        self.edit("security.md", "| CTL-04 | Token signature and expiry verified in the backend | API | EXISTING | THR-03 | TC-04, TC-05 | — |",
                  "| CTL-04 | Token signature and expiry verified in the backend | API | MISSING | THR-03 | TC-04, TC-05 | T-03 |")
        self.edit("spec.md", "| T-02 | Generic", "| T-03 | Verify token expiry | SR-03 | CTL-04 | TODO | — |\n| T-02 | Generic")
        self.declare("IMPLEMENTED")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("IMPLEMENTED", result.computed)

    def test_relevant_threat_without_controls(self):
        self.edit("security.md", "| LOW | HIGH | MEDIUM | CTL-04 |", "| LOW | HIGH | MEDIUM | CTL-05 |")
        self.assertError(self.validate(), "E13", "THR-03")

    def test_underestimated_risk(self):
        self.edit("security.md", "| MEDIUM | HIGH | HIGH | CTL-01, CTL-02 |", "| MEDIUM | HIGH | LOW | CTL-01, CTL-02 |")
        self.assertError(self.validate(), "E31", "THR-01")

    def test_mitigated_risk_with_missing_controls(self):
        self.edit("security.md", "| CTL-01 | The query filters by the token holder | BACKEND | EXISTING |",
                  "| CTL-01 | The query filters by the token holder | BACKEND | MISSING |")
        self.assertError(self.validate(), "E30", "RISK-01")

    def test_mobile_trigger_requires_mobile_controls(self):
        self.edit("spec.md", "| Storage or processing on a mobile device | NO |", "| Storage or processing on a mobile device | YES |")
        self.assertError(self.validate(), "E13", "MOBILE")

    def test_abuse_case_without_test(self):
        self.edit("spec.md", "| 404 with no data | TC-02 |", "| 404 with no data | — |")
        self.assertError(self.validate(), "E10", "AB-01")

    def test_security_design_without_controls(self):
        self.edit("spec.md", "| The query filters by the token subject | CTL-01 |", "| The query filters by the token subject | — |")
        self.edit("spec.md", "| Another holder's resource answers 404 | CTL-02 |", "| Another holder's resource answers 404 | — |")
        self.edit("spec.md", "| Transport over TLS 1.2 or higher | CRY-01 |", "| Transport over TLS 1.2 or higher | — |")
        self.assertError(self.validate(), "E05", "security design decisions")


class DataAndPrivacy(Scenario):
    def test_restricted_data_without_lifecycle(self):
        self.cut("security.md", "### DATA-02 · Token", "## 3. Actors")
        self.assertError(self.validate(), "E14", "DATA-02")

    def test_empty_lifecycle_field(self):
        self.edit("security.md", "| How long it is kept | 15 minutes |", "| How long it is kept | <fill> |")
        self.assertError(self.validate(), "E14", "how long")

    def test_unknown_protection_prevents_verification(self):
        self.edit("security.md", "| Copies, caches and backups | None |", "| Copies, caches and backups | UNKNOWN |")
        result = self.validate()
        self.assertEqual("IMPLEMENTED", result.computed)
        self.assertError(result, "E23", "SECURITY_VERIFIED exceeds")

    def test_personal_data_misclassified(self):
        self.edit("security.md", "| DATA-01 | Policy number and coverage | CONFIDENTIAL |", "| DATA-01 | Policy number and coverage | INTERNAL |")
        self.assertError(self.validate(), "E14", "CONFIDENTIAL")

    def test_data_without_protecting_requirement(self):
        self.edit("spec.md", "| DATA-02, THR-03 | CTL-04 |", "| THR-03 | CTL-04 |")
        self.assertError(self.validate(), "E15", "DATA-02")

    def test_compliance_claim(self):
        self.edit("spec.md", "### Goals and non-goals\n", "### Goals and non-goals\n\nThe system is fully compliant with the data protection law.\n")
        self.assertError(self.validate(), "E32")

    def test_certification_claim(self):
        self.edit("spec.md", "### Goals and non-goals\n", "### Goals and non-goals\n\nThe API is certified against ASVS level 2.\n")
        self.assertError(self.validate(), "E32")

    def test_stating_non_compliance_is_not_a_claim(self):
        self.edit("spec.md", "### Goals and non-goals\n", "### Goals and non-goals\n\nRetention does not comply with the policy yet.\n")
        self.assertNotIn("E32", self.codes(self.validate()))

    def test_tls_certificate_is_not_a_claim(self):
        self.edit("security.md", "| Recovery | Certificate reissue |", "| Recovery | Certificate reissued by the provider |")
        self.assertNotIn("E32", self.codes(self.validate()))

    def test_real_looking_personal_data_warns(self):
        self.edit("spec.md", "| Malicious insured |", "| Malicious insured (john.doe@gmail.com, 3001234567) |")
        warnings = {f.code for f in self.validate().warnings}
        self.assertIn("W01", warnings)
        self.assertIn("W02", warnings)


class Cryptography(Scenario):
    def test_restricted_without_mechanism(self):
        self.edit("security.md", "| Protects | DATA-01, DATA-02 |", "| Protects | DATA-01 |")
        self.edit("security.md", "| Protects | DATA-02 |", "| Protects | DATA-01 |")
        self.assertError(self.validate(), "E16", "DATA-02")

    def test_password_with_reversible_encryption(self):
        self.edit("security.md", "| Type | MAC |", "| Type | PASSWORD_HASH |")
        self.edit("security.md", "| Algorithm or service | HMAC-SHA256 (HS256) |", "| Algorithm or service | AES-256-GCM |")
        self.assertError(self.validate(), "E17", "password hashing")

    def test_hmac_declared_as_signature(self):
        self.edit("security.md", "| Type | MAC |", "| Type | SIGNATURE |")
        self.assertError(self.validate(), "E17", "not a digital signature")

    def test_weak_algorithm(self):
        self.edit("security.md", "| Algorithm or service | HMAC-SHA256 (HS256) |", "| Algorithm or service | HMAC-MD5 |")
        self.assertError(self.validate(), "E17", "MD5")

    def test_custom_algorithm(self):
        self.edit("security.md", "| Algorithm or service | HMAC-SHA256 (HS256) |", "| Algorithm or service | HMAC with a custom scheme |")
        self.assertError(self.validate(), "E17", "custom")

    def test_incomplete_mechanism(self):
        self.edit("security.md", "| Rotation | Every 90 days or on suspected leak |", "| Rotation | <fill> |")
        self.assertError(self.validate(), "E16", "rotation")

    def test_bcrypt_is_accepted_with_warning(self):
        self.edit("security.md", "| Type | MAC |", "| Type | PASSWORD_HASH |")
        self.edit("security.md", "| Algorithm or service | HMAC-SHA256 (HS256) |", "| Algorithm or service | bcrypt, cost 12 |")
        result = self.validate()
        self.assertNotIn("E17", self.codes(result))
        self.assertIn("W06", {f.code for f in result.warnings})


class TestCasesAndEvidence(Scenario):
    def test_pass_without_evidence(self):
        self.edit("test-cases.md", "| Evidence | EV-02 |", "| Evidence | — |")
        self.assertError(self.validate(), "E19", "TC-05")

    def test_evidence_cites_missing_test(self):
        self.edit("test-cases.md", "| Tool or method | pytest tests/test_policies.py::test_error_hides_personal_data |",
                  "| Tool or method | pytest tests/test_policies.py::test_nobody_wrote |")
        self.assertError(self.validate(), "E20", "test_nobody_wrote")

    def test_evidence_with_quoted_test_name(self):
        (self.repo / "tests" / "PoliciesTest.kt").write_text("fun `another insured cannot read the policy`() {}\n", encoding="utf-8")
        self.edit("test-cases.md", "| Evidence | tests/test_policies.py::test_other_user_gets_404 in the CI run |",
                  '| Evidence | tests/PoliciesTest.kt::"another insured cannot read the policy" in CI |')
        self.assertNoErrors(self.validate())
        self.edit("test-cases.md", '::"another insured cannot read the policy"', '::"a test that does not exist"')
        self.assertError(self.validate(), "E20", "a test that does not exist")

    def test_evidence_cites_missing_file(self):
        self.edit("gate.md", "| tests/test_policies.py | AVAILABLE |", "| tests/missing.py | AVAILABLE |")
        self.assertError(self.validate(), "E20", "tests/missing.py")

    def test_incomplete_test_case(self):
        self.edit("test-cases.md", "| Preconditions | A malformed policy number |", "| Preconditions | |")
        self.assertError(self.validate(), "E18", "TC-03")

    def test_security_test_without_risk(self):
        self.edit("test-cases.md", "| Risk covered | THR-02 |", "| Risk covered | — |")
        self.assertError(self.validate(), "E18", "TC-03")

    def test_manual_test_without_reproducible_steps(self):
        self.edit("test-cases.md", "| Procedure | 1. Call the API over HTTP. 2. Check it redirects to HTTPS. 3. Check the negotiated TLS version |",
                  "| Procedure | Check that everything is fine |")
        self.assertError(self.validate(), "E18", "numbered steps")

    def test_production_test_without_authorization(self):
        self.edit("test-cases.md", "| Environment | STAGING |", "| Environment | PRODUCTION |")
        self.assertError(self.validate(), "E29", "TC-05")

    def test_pending_security_test_leaves_tests_pending(self):
        self.edit("test-cases.md", "| Evidence | EV-02 |\n| Status | PASS |", "| Evidence | PENDING |\n| Status | PENDING |")
        result = self.validate()
        self.assertEqual("SECURITY_TESTS_PENDING", result.computed)
        self.assertError(result, "E23")
        self.declare("SECURITY_TESTS_PENDING")
        self.assertNoErrors(self.validate())

    def test_failing_security_test_blocks(self):
        self.edit("test-cases.md", "| Evidence | EV-02 |\n| Status | PASS |", "| Evidence | EV-02 |\n| Status | FAIL |")
        result = self.validate()
        self.assertEqual("BLOCKED", result.computed)
        self.assertError(result, "E23", "BLOCKED")

    def test_applicable_category_without_tests(self):
        self.edit("test-cases.md", "| User without permissions | YES | TC-02 |", "| User without permissions | YES | — |")
        self.assertError(self.validate(), "E10", "without permissions")

    def test_missing_category(self):
        self.edit("test-cases.md", "| Race conditions | NO | — | Read-only |\n", "")
        self.assertError(self.validate(), "E04", "race")


class QualityAndLevels(Scenario):
    def test_quality_requirement_without_test_case(self):
        self.edit("test-cases.md", "| Covers | QR-01 |", "| Covers | AC-01 |")
        self.assertError(self.validate(), "E33", "QR-01")

    def test_performance_requirement_needs_a_performance_test(self):
        self.edit("test-cases.md", "| Level | PERFORMANCE |", "| Level | INTEGRATION |")
        self.assertError(self.validate(), "E36", "QR-01")

    def test_accessibility_requirement_needs_an_accessibility_test(self):
        self.edit("spec.md", "| QR-01 | PERFORMANCE |", "| QR-01 | ACCESSIBILITY |")
        self.assertError(self.validate(), "E36", "ACCESSIBILITY")
        self.edit("test-cases.md", "| Level | PERFORMANCE |", "| Level | ACCESSIBILITY |")
        self.assertNoErrors(self.validate())

    def test_quality_requirement_needs_a_target(self):
        self.edit("spec.md", "| p95 under 300 ms and under 1% errors at 20 requests/s for 5 minutes in the test environment |", "| <fill> |")
        self.assertError(self.validate(), "E05", "target")

    def test_invalid_quality_category(self):
        self.edit("spec.md", "| QR-01 | PERFORMANCE |", "| QR-01 | SPEED |")
        self.assertError(self.validate(), "E27", "SPEED")

    def test_quality_section_may_be_not_applicable(self):
        self.cut("spec.md", "| ID | Category | Requirement |", "### Security triggers")
        self.edit("spec.md", "### Quality requirements\n", "### Quality requirements\n\nN/A: read-only listing with no new load or interface.\n\n")
        self.edit("test-cases.md", "| Covers | QR-01 |", "| Covers | AC-01 |")
        self.edit("test-cases.md", "| Kind | QUALITY |", "| Kind | FUNCTIONAL |")
        self.assertNoErrors(self.validate())

    def test_missing_quality_section(self):
        self.edit("spec.md", "### Quality requirements", "### Notes")
        self.assertError(self.validate(), "E02", "Quality requirements")

    def test_invalid_level(self):
        self.edit("test-cases.md", "| Level | PERFORMANCE |", "| Level | STRESS |")
        self.assertError(self.validate(), "E27", "STRESS")

    def test_level_is_required(self):
        self.edit("test-cases.md", "| Level | PERFORMANCE |", "| Level | |")
        self.assertError(self.validate(), "E18", "level")

    def test_invalid_kind(self):
        self.edit("test-cases.md", "| Kind | QUALITY |", "| Kind | LOAD |")
        self.assertError(self.validate(), "E27", "LOAD")

    def test_pending_quality_test_keeps_work_in_progress(self):
        self.edit("test-cases.md", "| Evidence | Load test summary of 2026-10-20 attached to the merge request: p95 210 ms, 0.1% errors |\n| Status | PASS |",
                  "| Evidence | PENDING |\n| Status | PENDING |")
        self.assertEqual("IN_PROGRESS", self.validate().computed)

    def test_interface_without_accessibility_requirement_warns(self):
        self.edit("spec.md", "| Web UI or data exposed in the browser | NO |", "| Web UI or data exposed in the browser | YES |")
        self.assertIn("W10", {f.code for f in self.validate().warnings})
        self.edit("spec.md", "| QR-01 | PERFORMANCE |", "| QR-01 | ACCESSIBILITY |")
        self.edit("test-cases.md", "| Level | PERFORMANCE |", "| Level | ACCESSIBILITY |")
        self.assertNotIn("W10", {f.code for f in self.validate().warnings})


class StoryFromTheBoard(Scenario):
    def test_the_story_is_copied_into_the_spec(self):
        self.cut("spec.md", "### User story", "### Problem and outcome")
        self.assertError(self.validate(), "E02", "User story")

    def test_the_story_cannot_stay_a_placeholder(self):
        self.edit("spec.md", "Como asegurado quiero ver mis pólizas vigentes para conocer mi cobertura.", "<fill: the story>")
        self.assertError(self.validate(), "E02", "User story")

    def test_criterion_source_is_stated_or_derived(self):
        self.edit("spec.md", "the policies they own | STATED |", "the policies they own | MAYBE |")
        self.assertError(self.validate(), "E27", "MAYBE")

    def test_derived_criterion_says_why(self):
        self.edit("spec.md", "| DERIVED: the story does not say how invalid input is answered |", "| DERIVED |")
        self.assertError(self.validate(), "E11", "AC-02")

    def test_some_criterion_comes_from_the_story(self):
        self.edit("spec.md", "the policies they own | STATED |", "the policies they own | DERIVED: implied by the title |")
        self.assertError(self.validate(), "E05", "STATED")

    def test_derived_criteria_need_tests_like_any_other(self):
        self.edit("test-cases.md", "| Covers | AC-02, SR-02 |", "| Covers | SR-02 |")
        self.assertError(self.validate(), "E33", "AC-02")


class Scenarios(Scenario):
    def test_every_use_case_has_scenarios(self):
        self.edit("spec.md", "| No policies: empty list |\n",
                  "| No policies: empty list |\n| UC-02 | Insured | Download a policy | 1. Opens it. 2. Downloads the PDF | No PDF yet |\n")
        self.assertError(self.validate(), "E37", "UC-02")

    def test_scenario_needs_a_disposition(self):
        self.edit("test-cases.md", "then both appear and nothing else | TC-01 |", "then both appear and nothing else | Pending |")
        self.assertError(self.validate(), "E37", "SC-01")

    def test_out_of_scope_needs_a_reason(self):
        self.edit("test-cases.md", "| OUT OF SCOPE: cancelled policies are shown by the cancellation story, not by this one |",
                  "| OUT OF SCOPE: no |")
        self.assertError(self.validate(), "E37", "SC-06")
        self.edit("test-cases.md", "| OUT OF SCOPE: no |", "| NEW STORY: list cancelled policies |")
        self.assertError(self.validate(), "E37", "SC-06")

    def test_scenario_comes_from_a_use_case_or_criterion(self):
        self.edit("test-cases.md", "| SC-03 | UC-01 |", "| SC-03 | — |")
        self.assertError(self.validate(), "E05", "SC-03")

    def test_scenarios_cannot_be_skipped_above_low(self):
        self.cut("test-cases.md", "| ID | From | Scenario | Disposition |", "## Scenario coverage")
        self.edit("test-cases.md", "## Scenarios\n", "## Scenarios\n\nN/A: the story is simple enough.\n\n")
        self.assertError(self.validate(), "E03", "Scenarios")

    def test_every_kind_is_reviewed(self):
        self.edit("test-cases.md", "| Limits and boundaries | YES | SC-04 | — |\n", "")
        self.assertError(self.validate(), "E04", "limits")

    def test_applicable_kind_cites_scenarios(self):
        self.edit("test-cases.md", "| Alternate flows | YES | SC-06 | — |", "| Alternate flows | YES | — | — |")
        self.assertError(self.validate(), "E37", "alternate")

    def test_kind_not_applicable_needs_a_rationale(self):
        self.edit("test-cases.md", "| NO | — | Read-only listing; sign-in and sign-out are unchanged and belong to their own stories |",
                  "| NO | — | — |")
        self.assertError(self.validate(), "E11", "related flows")

    def test_authorization_requires_several_users(self):
        self.edit("test-cases.md", "| Several users, sessions, devices or roles | YES | SC-02 | — |",
                  "| Several users, sessions, devices or roles | NO | — | Only one insured at a time |")
        self.assertError(self.validate(), "E37", "several users")

    def test_authentication_requires_related_flows(self):
        self.edit("spec.md", "| Authentication, sessions, credentials or one-time codes | NO |",
                  "| Authentication, sessions, credentials or one-time codes | YES |")
        self.assertError(self.validate(), "E37", "related flows")

    def test_coverage_cannot_cite_undefined_scenarios(self):
        self.edit("test-cases.md", "| Main flow | YES | SC-01 | — |", "| Main flow | YES | SC-09 | — |")
        result = self.validate()
        self.assertError(result, "E07", "SC-09")
        self.assertError(result, "E37", "main flow")


class DependenciesAndRisks(Scenario):
    def test_evaluated_dependency_without_date(self):
        self.edit("security.md", "| OSV.dev 2026-10-20 |", "| Reviewed |")
        self.assertError(self.validate(), "E21", "DEP-01")

    def test_pending_dependency_prevents_verification(self):
        self.edit("security.md", "| No known vulnerabilities | EVALUATED |", "| — | PENDING |")
        result = self.validate()
        self.assertEqual("IMPLEMENTED", result.computed)
        self.assertError(result, "E23")

    def test_open_critical_risk_blocks(self):
        self.edit("security.md", "| THR-01 | LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |",
                  "| THR-01 | HIGH | CRITICAL | CRITICAL | MITIGATE | Critical until fixed | OPEN |")
        result = self.validate()
        self.assertEqual("BLOCKED", result.computed)
        self.assertError(result, "E23", "BLOCKED")

    def test_ai_cannot_accept_risk(self):
        self.edit("security.md", "| LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |",
                  "| MEDIUM | MEDIUM | MEDIUM | ACCEPT | Medium | ACCEPTED |")
        self.edit("gate.md", "| Risk | Decision | Approved by | Role | Date | Expires |\n|---|---|---|---|---|---|",
                  "| Risk | Decision | Approved by | Role | Date | Expires |\n|---|---|---|---|---|---|\n"
                  "| RISK-01 | Accept | Claude Code | AI agent | 2026-10-20 | 2026-12-31 |")
        result = self.validate()
        self.assertError(result, "E22", "never an AI agent")
        self.assertNotEqual("RISK_ACCEPTED", result.computed)

    def test_accepted_risk_without_approval(self):
        self.edit("security.md", "| LOW | LOW | LOW | MITIGATE | Low: uniform 404 | MITIGATED |",
                  "| MEDIUM | MEDIUM | MEDIUM | ACCEPT | Medium | ACCEPTED |")
        self.assertError(self.validate(), "E22", "RISK-01")

    def test_pending_blocking_decision(self):
        self.edit("security.md", "N/A: no pending decisions.",
                  "| ID | Decision | Options | Recommendation | Decider | Blocks gate | Status |\n|---|---|---|---|---|---|---|\n"
                  "| DEC-01 | SMS provider | A or B | A | Tech lead | YES | PENDING |")
        self.declare("IMPLEMENTED")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("IMPLEMENTED", result.computed)


class ReviewAndGate(Scenario):
    def test_no_human_review(self):
        self.edit("gate.md", "| Ana Reviewer | Tech lead | 2026-10-20 | Full package and PR | APPROVED |\n", "")
        result = self.validate()
        self.assertEqual("SECURITY_REVIEW_PENDING", result.computed)
        self.assertError(result, "E23")

    def test_review_signed_by_an_agent(self):
        self.edit("gate.md", "| Ana Reviewer | Tech lead |", "| Codex | Automated reviewer |")
        result = self.validate()
        self.assertError(result, "E26")
        self.assertNotIn(result.computed, ("SECURITY_VERIFIED", "RISK_ACCEPTED"))
        self.assertTrue(any("human security review" in m for _, m in result.reasons))

    def test_critical_profile_needs_two_reviewers(self):
        self.edit("spec.md", "| Security profile | HIGH |", "| Security profile | CRITICAL |")
        self.assertEqual("SECURITY_REVIEW_PENDING", self.validate().computed)

    def test_unknown_state(self):
        self.declare("SAFE")
        self.assertError(self.validate(), "E27", "SAFE")

    def test_open_functional_task_keeps_in_progress(self):
        self.edit("spec.md", "| CTL-01, CTL-02 | DONE |", "| CTL-01, CTL-02 | IN_PROGRESS |")
        self.declare("IN_PROGRESS")
        result = self.validate()
        self.assertNoErrors(result)
        self.assertEqual("IN_PROGRESS", result.computed)

    def test_done_task_without_evidence(self):
        self.edit("spec.md", "| DONE | commit 1a2b3c4 |", "| DONE | — |")
        self.assertError(self.validate(), "E28", "T-02")

    def test_done_spec_without_closeout(self):
        self.edit("spec.md", "| Status | IN_REVIEW |", "| Status | DONE |")
        self.assertError(self.validate(), "E34", "AC-01")

    def test_done_spec_with_unmet_criterion(self):
        self.edit("spec.md", "| Status | IN_REVIEW |", "| Status | DONE |")
        self.edit("gate.md", "| Criterion | Result | Evidence |\n|---|---|---|",
                  "| Criterion | Result | Evidence |\n|---|---|---|\n| AC-01 | PARTIAL | tests/test_policies.py |")
        self.assertError(self.validate(), "E34", "not MET")

    def test_done_spec_with_unverified_gate(self):
        self.edit("spec.md", "| Status | IN_REVIEW |", "| Status | DONE |")
        self.edit("gate.md", "| Criterion | Result | Evidence |\n|---|---|---|",
                  "| Criterion | Result | Evidence |\n|---|---|---|\n| AC-01 | MET | tests/test_policies.py |")
        self.edit("gate.md", "| Ana Reviewer | Tech lead | 2026-10-20 | Full package and PR | APPROVED |\n", "")
        self.declare("SECURITY_REVIEW_PENDING")
        self.assertError(self.validate(), "E35", "SECURITY_REVIEW_PENDING")


class SecretsAndPaths(Scenario):
    def test_secret_in_package_blocks_without_printing_it(self):
        value = "AKIA" + "Q7RZ" * 4
        self.edit("spec.md", "No new variables.", f"No new variables. Key used in tests: {value}")
        result = self.validate()
        self.assertError(result, "E25")
        self.assertEqual("BLOCKED", result.computed)
        output = "\n".join(str(f) for f in result.findings) + "\n".join(m for _, m in result.reasons)
        self.assertNotIn(value, output)
        self.assertNotIn(value[4:], output)

    def test_critical_path_requires_trigger(self):
        self.edit("spec.md", "| backend/app/modules/policy/query.py |", "| backend/app/modules/identity/service.py |")
        self.assertError(self.validate(), "E24", "is a critical path")

    def test_declared_critical_path_passes(self):
        self.edit("spec.md", "| backend/app/modules/policy/query.py |", "| backend/app/modules/identity/** |")
        self.edit("spec.md", "| Critical paths (sdd/security/critical-paths.md) | NO |", "| Critical paths (sdd/security/critical-paths.md) | YES |")
        self.assertNoErrors(self.validate())


class MultiTenant(Scenario):
    def test_multi_tenant_requires_isolation_and_negative_tests(self):
        self.edit("spec.md", "| Multiple tenants, partners or organizations | NO |", "| Multiple tenants, partners or organizations | YES |")
        result = self.validate()
        self.assertError(result, "E03", "multi-tenancy")
        self.assertError(result, "E10", "cross-tenant")


if __name__ == "__main__":
    unittest.main()
