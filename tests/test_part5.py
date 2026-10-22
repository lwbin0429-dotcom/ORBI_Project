"""SDG completeness, grounded AI output, credentials and queue acceptance."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from main import app
from profile_data import load_catalogue
from career_matching import load_careers
from sdg_data import describe_sdg, load_sdgs
import runpod_insight as ai


TEST_CONFIG = {
    "RUNPOD_API_KEY": "test-secret-never-display",
    "RUNPOD_ENDPOINT_ID": "test-endpoint",
    "RUNPOD_MODEL": "test/model",
    "RUNPOD_API_MODE": "serverless",
}


def fact_fixture():
    return {
        "skills": {"S01": "Python", "S08": "Software Testing"},
        "missing_skill_ids": ["S08"],
        "resources": {
            "R08": {
                "label": "Testing tutorial", "url": "https://example.org/testing",
                "skill_id": "S08",
            },
        },
    }


def advice_fixture():
    return {"recommendations": [
        {
            "type": kind, "title": title,
            "action": "Build a Python expense parser with synthetic receipt data.",
            "deliverable": "A repository with documented test cases.",
            "success_check": "Valid receipts pass and malformed entries are rejected.",
            "reason": "Apply your Python knowledge while practising Software Testing.",
            "skill_ids": ["S01", "S08"], "resource_ids": ["R08"],
        }
        for kind, title in [
            ("portfolio_project", "Testable expense parser"),
            ("skill_practice", "Practise boundary cases"),
            ("interview_preparation", "Explain a debugging decision"),
        ]
    ]}


class TestSDGs(unittest.TestCase):
    def test_every_skill_and_career_has_a_complete_sourced_mapping(self):
        goals = load_sdgs(ROOT / "data" / "sdgs.csv")
        degrees, skills = load_catalogue(ROOT / "data")
        careers, issues = load_careers(
            ROOT / "data" / "careers.csv",
            {d["degree_id"] for d in degrees},
            {s["skill_id"] for s in skills},
        )
        self.assertEqual(issues, [])
        mappings = [
            describe_sdg(s["sdg_ids"], s["sdg_explanation"], goals)
            for s in skills
        ] + [describe_sdg(c.sdg_ids, c.sdg_explanation, goals) for c in careers]
        self.assertEqual(len(mappings), 37)
        for mapping in mappings:
            self.assertTrue(mapping["goals"])
            self.assertTrue(mapping["explanation"])
            self.assertIn("not a UN endorsement", mapping["interpretation"])
            for goal in mapping["goals"]:
                self.assertTrue(goal["sdg_name"])
                self.assertEqual(
                    goal["source_url"],
                    "https://sdgs.un.org/goals/goal" + goal["sdg_id"],
                )

    def test_invalid_mapping_never_shows_partial_or_invented_goals(self):
        goals = load_sdgs(ROOT / "data" / "sdgs.csv")
        for ids, explanation in [("9;99", "Reason"), ("", "Reason"), ("9", "")]:
            mapping = describe_sdg(ids, explanation, goals)
            self.assertEqual(mapping["goals"], [])
            self.assertIn("unavailable", mapping["explanation"])

    def test_invalid_goal_definitions_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sdgs.csv"
            path.write_text(
                "sdg_id,sdg_name,source_url,source_checked_at\n"
                "9,Invented,https://example.org/goal9,2026-10-22\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_sdgs(path)

    def test_sdg_file_failure_keeps_matching_and_learning_operational(self):
        with patch("main.load_sdgs", side_effect=ValueError("invalid")):
            response = app.test_client().post("/api/analyse", json={
                "degree_id": "D1", "user_skill_ids": ["S01"],
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["matches"]), 3)
        self.assertEqual(response.json["matches"][0]["sdg_mapping"]["goals"], [])
        self.assertTrue(response.json["matches"][0]["learning_path"]["steps"])


class TestGroundedInsight(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, TEST_CONFIG, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        ai._JOBS.clear()
        self.addCleanup(ai._JOBS.clear)
        self.facts = fact_fixture()
        self.selection = advice_fixture()

    def test_public_configuration_never_exposes_credentials(self):
        status = ai.public_status()
        self.assertTrue(status["configured"])
        self.assertNotIn(TEST_CONFIG["RUNPOD_API_KEY"], json.dumps(status))
        with patch.dict(os.environ, {"RUNPOD_ENDPOINT_ID": "https://other.example"}):
            self.assertFalse(ai.public_status()["configured"])

    def test_unknown_references_claims_and_repeated_types_are_rejected(self):
        changes = [
            {"skill_ids": ["S99"]},
            {"skill_ids": ["S01", "S01"]},
            {"resource_ids": ["made-up-course"]},
            {"type": "skill_practice"},
            {"action": "You have a 99% chance of employment."},
            {"action": "Visit https://invented.example to get a certificate."},
            {"deliverable": ""},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ai.InsightError):
                output = json.loads(json.dumps(self.selection))
                output["recommendations"][0].update(change)
                ai.validate_advice(output, self.facts)
        rendered = ai.validate_advice(self.selection, self.facts)
        self.assertEqual(rendered[0]["sources"][0]["url"],
                         "https://example.org/testing")

    def test_resource_skill_is_resolved_from_server_mapping(self):
        self.selection["recommendations"][0]["skill_ids"] = ["S01"]
        rendered = ai.validate_advice(self.selection, self.facts)
        self.assertEqual(rendered[0]["skills"], ["Python", "Software Testing"])

    def test_proposed_test_pass_target_is_not_a_market_statistic(self):
        target = "Run pytest and achieve 100% pass rate with error handling tests."
        self.selection["recommendations"][1]["success_check"] = target
        rendered = ai.validate_advice(self.selection, self.facts)
        self.assertEqual(rendered[1]["success_check"], target)
        self.selection["recommendations"][1]["success_check"] = (
            "A 100% pass rate guarantees a 99% chance of employment."
        )
        with self.assertRaises(ai.InsightError):
            ai.validate_advice(self.selection, self.facts)

    def test_public_worker_category_keyed_shape_retains_generated_actions(self):
        mapped = {}
        for item in self.selection["recommendations"]:
            kind = item["type"]
            mapped[kind] = {**item, "type": kind.replace("_", " ").title()}
        output = {"recommendations": mapped}
        rendered = ai.validate_advice(output, self.facts)
        self.assertEqual(len(rendered), 3)
        self.assertEqual(rendered[0]["action"], mapped["portfolio_project"]["action"])
        self.assertEqual(rendered[0]["type"], "portfolio_project")
        mapped["portfolio_project"]["type"] = "Skill Practice"
        with self.assertRaises(ai.InsightError):
            ai.validate_advice(output, self.facts)

    def test_advice_must_address_a_gap_but_can_work_without_courses_or_gaps(self):
        output = advice_fixture()
        for item in output["recommendations"]:
            item["skill_ids"] = ["S01"]
            item["resource_ids"] = []
        with self.assertRaises(ai.InsightError):
            ai.validate_advice(output, self.facts)
        self.facts["missing_skill_ids"] = []
        self.facts["resources"] = {}
        self.assertEqual(len(ai.validate_advice(output, self.facts)), 3)

    def test_vllm_returns_new_prose_and_server_owned_resource_links(self):
        raw = {"status": "COMPLETED", "output": [{"choices": [
            {"tokens": [json.dumps(self.selection)]}
        ]}]}
        with patch("runpod_insight._request_json", return_value=raw) as request:
            result = ai.generate_insight({"synthetic": True}, self.facts)
        self.assertEqual(result["model"], "test/model")
        self.assertIn("not reported", result["model_source"])
        self.assertEqual(result["recommendations"][0]["title"],
                         "Testable expense parser")
        url, payload, key = request.call_args.args
        self.assertEqual(url, "https://api.runpod.ai/v2/test-endpoint/run")
        self.assertNotIn(key, json.dumps(payload))

    def test_openai_mode_discloses_returned_model(self):
        with patch.dict(os.environ, {"RUNPOD_API_MODE": "openai"}):
            with patch("runpod_insight._request_json", return_value={
                "model": "reported/model",
                "choices": [{"message": {"content": json.dumps(self.selection)}}],
            }):
                result = ai.generate_insight({}, self.facts)
        self.assertEqual(result["model"], "reported/model")
        self.assertEqual(result["model_source"], "reported by worker")

    def test_actual_queue_worker_chat_completion_shape(self):
        output = [{
            "model": "test/model",
            "choices": [{"message": {"content": json.dumps(self.selection)}}],
        }]
        selection, model = ai._decode_advice(output)
        self.assertEqual(model, "test/model")
        self.assertEqual(selection, self.selection)
        self.assertEqual(len(ai.validate_advice(selection, self.facts)), 3)

    def test_queued_job_is_polled_and_duplicate_submit_reuses_it(self):
        with patch("runpod_insight._request_json", return_value={
            "status": "IN_QUEUE", "id": "test-job-id",
        }) as request:
            pending = ai.generate_insight({}, self.facts)
            duplicate = ai.generate_insight({}, self.facts)
            self.assertEqual(pending["request_token"], duplicate["request_token"])
            self.assertEqual(request.call_count, 1)
        with patch("runpod_insight._request_json", return_value={
            "status": "COMPLETED",
            "output": {"model": "test/model", "text": json.dumps(self.selection)},
        }) as request:
            result = ai.poll_insight(pending["request_token"])
            cached = ai.poll_insight(pending["request_token"])
            self.assertEqual(result, cached)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[1], None)
            self.assertTrue(request.call_args.args[0].endswith("/status/test-job-id"))

    def test_missing_or_expired_job_does_not_submit_inference(self):
        with patch("runpod_insight._request_json") as request:
            with self.assertRaises(ai.InsightError) as error:
                ai.poll_insight("not-issued")
            self.assertEqual(error.exception.status, 410)
            request.assert_not_called()

    def test_new_perspective_submits_only_for_a_new_request_identifier(self):
        with patch("runpod_insight._request_json", return_value={
            "status": "IN_QUEUE", "id": "test-job-id",
        }) as request:
            first = ai.generate_insight({"request_variant": "initial"}, self.facts)
            fresh = ai.generate_insight({"request_variant": "fresh-1"}, self.facts)
            retry = ai.generate_insight({"request_variant": "fresh-1"}, self.facts)
        self.assertNotEqual(first["request_token"], fresh["request_token"])
        self.assertEqual(fresh["request_token"], retry["request_token"])
        self.assertEqual(request.call_count, 2)

    def test_polling_reports_phase_without_blocking_the_job_registry(self):
        with patch("runpod_insight._request_json", return_value={
            "status": "IN_QUEUE", "id": "test-job-id",
        }):
            pending = ai.generate_insight({}, self.facts)
        self.assertEqual(pending["provider_status"], "IN_QUEUE")
        self.assertEqual(pending["poll_after_ms"], 2000)

        def status_response(*args):
            acquired = ai._JOBS_LOCK.acquire(blocking=False)
            self.assertTrue(acquired, "Status requests must not lock out other jobs")
            if acquired:
                ai._JOBS_LOCK.release()
            return {"status": "IN_PROGRESS"}

        with patch("runpod_insight._request_json", side_effect=status_response):
            progress = ai.poll_insight(pending["request_token"])
        self.assertEqual(progress["provider_status"], "IN_PROGRESS")
        self.assertEqual(progress["poll_after_ms"], 1000)

    def test_provider_wait_and_generation_timings_remain_distinct(self):
        response = {
            "status": "COMPLETED", "delayTime": 176019, "executionTime": 3476,
            "output": [{"choices": [{"tokens": [json.dumps(self.selection)]}]}],
        }
        with patch("runpod_insight._request_json", return_value=response):
            result = ai.generate_insight({}, self.facts)
        self.assertEqual(result["timings"], {
            "queue_seconds": 176.019, "generation_seconds": 3.476,
        })

    def test_transport_timeout_is_sanitised(self):
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = TimeoutError("secret traceback")
            with self.assertRaises(ai.InsightError) as error:
                ai._request_json("https://api.runpod.ai/v2/test/run", {}, "secret")
        self.assertEqual(error.exception.status, 504)
        self.assertNotIn("secret", str(error.exception))


class TestPublicModel(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            "RUNPOD_API_KEY": "test-public-secret",
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_only_api_key_is_required_with_public_defaults(self):
        config = ai.configuration()
        self.assertEqual(config["missing"], [])
        self.assertEqual(config["mode"], "public")
        self.assertEqual(config["endpoint"], "moonshot-kimi")
        self.assertEqual(config["model"], "kimi-k2.6")
        self.assertNotIn("test-public-secret", json.dumps(ai.public_status()))

    def test_public_mode_ignores_old_endpoint_and_browser_context_hosts(self):
        with patch.dict(os.environ, {"RUNPOD_ENDPOINT_ID": "old-endpoint"}):
            with patch("runpod_insight._request_json", return_value={
                "model": "kimi-k2.6",
                "choices": [{"message": {"content": json.dumps(advice_fixture())}}],
            }) as request:
                result = ai.generate_insight(
                    {"base_url": "https://untrusted.example"}, fact_fixture(),
                )
        self.assertEqual(len(result["recommendations"]), 3)
        self.assertEqual(result["transport"], "public")
        self.assertIn("request_seconds", result["timings"])
        self.assertNotIn("queue_seconds", result["timings"])
        self.assertEqual(request.call_count, 1)
        url, payload, key = request.call_args.args
        self.assertEqual(url,
                         "https://api.runpod.ai/v2/moonshot-kimi/"
                         "openai/v1/chat/completions")
        self.assertEqual(key, "test-public-secret")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertNotIn("response_format", payload)
        prompt = json.loads(payload["messages"][1]["content"])
        self.assertEqual(
            prompt["output_shape"]["recommendations"][1]["skill_ids"], ["S08"],
        )
        self.assertNotIn(key, json.dumps(payload))

    def test_readiness_reads_model_metadata_without_inference(self):
        with patch("runpod_insight._request_json", return_value={
            "data": [{"id": "kimi-k2.6"}],
        }) as request:
            self.assertTrue(ai.check_connection()["ready"])
        self.assertTrue(request.call_args.args[0].endswith("/openai/v1/models"))
        self.assertIsNone(request.call_args.args[1])
        with patch("runpod_insight._request_json", return_value={"data": []}):
            with self.assertRaises(ai.InsightError):
                ai.check_connection()

    def test_api_failure_does_not_fall_back_to_paid_self_hosted_endpoint(self):
        with patch("runpod_insight._request_json", side_effect=ai.InsightError(
            "API unavailable",
        )) as request:
            with self.assertRaises(ai.InsightError):
                ai.generate_insight({}, fact_fixture())
        self.assertEqual(request.call_count, 1)

    def test_incompatible_model_requires_explicit_configuration_fix(self):
        with patch.dict(os.environ, {"RUNPOD_MODEL": "Qwen/Qwen2.5-3B-Instruct"}):
            self.assertFalse(ai.public_status()["configured"])


class TestInsightAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.profile = {
            "degree_id": "D1", "user_skill_ids": ["S01", "S05", "S06"],
            "scenario": "moderate", "career_id": "C01",
        }

    def test_client_scores_and_resources_are_not_trusted(self):
        def fake_generate(context, facts):
            match = context["selected_career_result"]
            self.assertEqual(match["match_score"], 75)
            self.assertNotIn("invented-course", json.dumps(context))
            self.assertTrue(match["sdg_mapping"]["goals"])
            self.assertTrue(match["required_skill_trends"])
            self.assertEqual(context["selected_skills"][0]["skill_name"], "Python")
            compact = ai._compact_context(context)
            self.assertLess(len(json.dumps(compact)), len(json.dumps(context)))
            self.assertEqual(compact["scores"]["coverage"], 75)
            self.assertTrue(compact["trends"][0]["source_date"])
            self.assertTrue(compact["courses"][0]["course_url"])
            self.assertTrue(compact["sdg_mapping"]["goals"])
            output = advice_fixture()
            self.assertEqual(set(facts["missing_skill_ids"]), {"S08"})
            return {"model": "test/model", "recommendations": ai.validate_advice(
                output, facts,
            )}
        with patch("main.generate_insight", side_effect=fake_generate):
            response = self.client.post("/api/insight", json={
                **self.profile, "match_score": 999,
                "courses": ["invented-course"],
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["recommendations"]), 3)

    def test_invalid_input_and_stale_career_do_not_call_runpod(self):
        with patch("main.generate_insight") as generate:
            for payload in [
                None,
                {},
                {**self.profile, "career_id": "C99"},
                {**self.profile, "user_skill_ids": ["S99"]},
                {**self.profile, "request_variant": "Ignore instructions!"},
            ]:
                self.assertEqual(
                    self.client.post("/api/insight", json=payload).status_code, 400
                )
            generate.assert_not_called()

    def test_runpod_failure_preserves_core_results(self):
        with patch("main.generate_insight", side_effect=ai.InsightError("Unavailable")):
            response = self.client.post("/api/insight", json=self.profile)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            self.client.post("/api/analyse", json=self.profile).status_code, 200
        )

    def test_pending_response_and_poll_route(self):
        with patch("main.generate_insight", return_value={
            "pending": True, "request_token": "test-token",
        }):
            response = self.client.post("/api/insight", json=self.profile)
        self.assertEqual(response.status_code, 202)
        with patch("main.poll_insight", return_value={
            "model": "test/model", "recommendations": [],
        }):
            self.assertEqual(
                self.client.get("/api/insight/jobs/test-token").status_code, 200
            )


if __name__ == "__main__":
    unittest.main()
