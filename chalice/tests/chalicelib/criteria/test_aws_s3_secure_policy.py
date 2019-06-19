from chalicelib.criteria.aws_s3_secure_policy import AwsS3SecurePolicy

from tests.chalicelib.criteria.test_criteria_default import (
    CriteriaSubclassTestCaseMixin,
    TestCaseWithAttrAssert,
)
from tests.chalicelib.criteria.test_data import S3_BUCKET_POLICY_BUCKETS
import json


class TestAwsS3SecurePolicy(CriteriaSubclassTestCaseMixin, TestCaseWithAttrAssert):
    @classmethod
    def setUpClass(cls):
        super(TestAwsS3SecurePolicy, cls).setUpClass()

        cls.test_data = S3_BUCKET_POLICY_BUCKETS

    def setUp(self):
        """
        """
        super(TestAwsS3SecurePolicy, self).setUp()
        self.subclass = AwsS3SecurePolicy(self.app)

    def test_init_client(self):
        self.assertIn("get_bucket_list", dir(self.subclass.client))
        self.assertIn("get_bucket_policy", dir(self.subclass.client))

    def test_get_data(self):
        self.subclass.client.get_bucket_list = lambda session: [{"Name": "bucket"}]
        self.subclass.client.get_bucket_policy = lambda session, bucket_name: json.dumps(
            "{}"
        )

        buckets = self.subclass.get_data(None)

        self.assertIsInstance(buckets, list, msg="Must return list")
        assert all([isinstance(item, dict) for item in buckets])
        self.assertIn("Policy", buckets[0], msg="The dictionary must have a Policy key")

    def test_translate(self):
        bucket = self.test_data[list(self.test_data)[0]]
        translation = self.subclass.translate(bucket)

        assert isinstance(translation, dict)

        assert "resource_id" in translation
        assert "resource_name" in translation

        assert translation["resource_id"] == f"arn:aws:s3:::{bucket['Name']}"
        assert translation["resource_name"] == bucket["Name"]

    def get_bucket_evaluation_result(self, test):
        return self._evaluate_invariant_assertions({}, self.test_data[test], [])

    def test_evaluate_pass_secure_transport_true(self):
        result = self.get_bucket_evaluation_result("pass_secure_transport_true")

        self._evaluate_passed_status_assertions(None, result)

    def test_evaluate_pass_secure_transport_false(self):
        result = self.get_bucket_evaluation_result("pass_secure_transport_true")

        self._evaluate_passed_status_assertions(None, result)

    def test_evaluate_pass_multiple_statements(self):
        result = self.get_bucket_evaluation_result("pass_multiple_statements")

        self._evaluate_passed_status_assertions(None, result)

    def test_evaluate_fail_multiple_statements(self):
        result = self.get_bucket_evaluation_result("fail_multiple_statements")

        self._evaluate_failed_status_assertions(None, result)

    def test_evaluate_fail_secure_transport_true(self):
        result = self.get_bucket_evaluation_result("fail_secure_transport_true")

        self._evaluate_failed_status_assertions(None, result)
        #self.assertIn("misconfigured", result["annotation"])

    def test_evaluate_fail_secure_transport_false(self):
        result = self.get_bucket_evaluation_result("fail_secure_transport_false")

        self._evaluate_failed_status_assertions(None, result)
        #self.assertIn("misconfigured", result["annotation"])

    def test_evaluate_fail_no_policy(self):
        result = self.get_bucket_evaluation_result("fail_no_policy")

        self._evaluate_failed_status_assertions(None, result)
        assert result["annotation"] == "Bucket does not enforce SecureTransport"

    def test_evaluate_fail_no_condition(self):
        result = self.get_bucket_evaluation_result("fail_no_condition")

        self._evaluate_failed_status_assertions(None, result)
        assert result["annotation"] == "Bucket does not enforce SecureTransport"

    def test_evaluate_fail_no_secure_condition(self):
        result = self.get_bucket_evaluation_result("fail_no_secure_condition")

        self._evaluate_failed_status_assertions(None, result)
        assert result["annotation"] == "Bucket does not enforce SecureTransport"

    def test_evaluate_fail_only_partly_secure(self):
        result = self.get_bucket_evaluation_result("fail_only_partly_secure")

        self._evaluate_failed_status_assertions(None, result)
        assert result["annotation"] == "Bucket does not enforce SecureTransport"

    def test_evaluate_fail_overridden_statement(self):
        result = self.get_bucket_evaluation_result("fail_overridden_statement")

        self._evaluate_failed_status_assertions(None, result)
        assert result["annotation"] == "Bucket does not enforce SecureTransport"
