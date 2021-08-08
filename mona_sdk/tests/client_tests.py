"""
Test module for client.py
"""
import unittest
from datetime import datetime
from unittest.mock import patch

from mona_sdk.client import Client, MonaSingleMessage
from mona_sdk.authentication import _get_auth_response_with_retries
from mona_sdk.client_exceptions import MonaExportException, MonaAuthenticationException

# This token (when decoded) contains this payload: {"tenantId": "test_tenant_id"}, so
# that client._get_user_id() function could work properly.
TEST_TOKEN = (
    "eyJhbGciOiJIUzI1NiJ9.eyJ0ZW5hbnRJZCI6InRlc3RfdGFuZW50X2lkIn0.d9lhbJi7pB"
    "ghbZ6YIr0sqy8E-KWxo1y6DtNjoMk4ikw"
)


class ClientTests(unittest.TestCase):
    @patch("mona_sdk.client.requests.request")
    def _init_test_client(
        self,
        mock_request,
        raise_export_exceptions=False,
        raise_authentication_exceptions=False,
    ):
        """
        :return: An initialized client.
        """
        mock_request.return_value.ok = True
        mock_request.return_value.json.return_value = {
            "accessToken": TEST_TOKEN,
            "refreshToken": "test_refresh_token",
            "expires": "Mon, 16 Feb 2099 15:26:22 GMT",
        }
        return Client(
            "",
            "",
            raise_export_exceptions=raise_export_exceptions,
            raise_authentication_exceptions=raise_authentication_exceptions,
        )

    @patch("mona_sdk.client.requests.request")
    def test_wrong_key_or_secret_with_exceptions(self, mock_request):
        """
        Asserts that initializing Mona's client with wrong/missing
        api key or secret will raise a MonaAuthenticationException when asked to (by
        setting RAISE_AUTHENTICATION_EXCEPTIONS to True).
        """
        mock_request.return_value.ok = False

        mock_request.return_value.json.return_value = {
            "errors": [
                "clientId must be a string",
                "secret must be a string",
            ]
        }
        with self.assertRaises(MonaAuthenticationException) as err:
            Client(None, None, raise_authentication_exceptions=True)
        self.assertEqual(
            "Mona's client could not authenticate. errors: clientId must be a string, "
            "secret must be a string",
            str(err.exception),
        )

        mock_request.return_value.json.return_value = {
            "errors": ["secret must be a string"]
        }
        with self.assertRaises(MonaAuthenticationException) as err:
            Client("<API_KEY>", None, raise_authentication_exceptions=True)
        self.assertEqual(
            "Mona's client could not authenticate. errors: secret must be a string",
            str(err.exception),
        )

        mock_request.return_value.json.return_value = {
            "errors": ["clientId must be a string"]
        }
        with self.assertRaises(MonaAuthenticationException) as err:
            Client(None, "<SECRET>", raise_authentication_exceptions=True)
        self.assertEqual(
            "Mona's client could not authenticate. errors: clientId must be a string",
            str(err.exception),
        )

        mock_request.return_value.json.return_value = {
            "errors": ["Invalid authentication"]
        }
        with self.assertRaises(MonaAuthenticationException) as err:
            Client("WRONG_KEY", "WRONG_SECRET", raise_authentication_exceptions=True)
        self.assertEqual(
            "Mona's client could not authenticate. errors: Invalid authentication",
            str(err.exception),
        )

    @patch("mona_sdk.client.requests.request")
    def test_wrong_key_or_secret_without_exceptions(self, mock_request):
        """
        Asserts that initializing Mona's client with wrong
        api key and secret when RAISE_AUTHENTICATION_EXCEPTIONS is false will return and
        Client.is_authenticated() will return the expected value.
        """

        mock_request.return_value.ok = False
        mock_request.return_value.json.return_value = {
            "errors": ["Invalid authentication"]
        }

        bad_client = Client("WRONG_KEY", "WRONG_SECRET")
        self.assertFalse(bad_client.is_active())

        good_client = self._init_test_client()
        self.assertTrue(good_client.is_active())

    @patch("mona_sdk.client.requests.request")
    def test_export_without_exception(self, mock_request):
        """
        Asserts an export() call with different parameters causes
        the correct response.
        """

        test_mona_client = self._init_test_client()
        good_message = {"a": "some data"}

        # Test a correct written message export.
        mock_request.return_value.ok = True
        res = test_mona_client.export(
            MonaSingleMessage(message=good_message, contextClass="TEST_CONTEXT_CLASS")
        )
        self.assertTrue(res)

        # Change mock rest-api response to a failed message export.
        mock_request.return_value.ok = False
        mock_request.return_value.json.return_value = {
            "failed": 1,
            "failure_reasons": {},
        }
        # Test an empty message export.
        res = test_mona_client.export(
            MonaSingleMessage(message=None, contextClass="TEST_CONTEXT_CLASS")
        )
        self.assertFalse(res)

        # Test an empty string context_class.
        res = test_mona_client.export(
            MonaSingleMessage(message=good_message, contextClass="")
        )
        self.assertFalse(res)

        # Test illegal export_timestamp type (must have 10/13 digits).
        res = test_mona_client.export(
            MonaSingleMessage(
                message=good_message,
                contextClass="TEST_CONTEXT_CLASS",
                exportTimestamp=12345678,
            )
        )
        self.assertFalse(res)

        # Test illegal context_id type (must be a string).
        res = test_mona_client.export(
            MonaSingleMessage(
                message=good_message,
                contextClass="TEST_CONTEXT_CLASS",
                contextId=12,
            )
        )
        self.assertFalse(res)

        # Test un-matching context_id and context_class: context_id cannot have
        # more '.' than context_class (wrong use of sub-contexts).
        res = test_mona_client.export(
            MonaSingleMessage(
                message=good_message,
                contextClass="TEST_CONTEXT_CLASS",
                contextId="TEST_CONTEXT_ID.SUB_CONTEXT",
            )
        )
        self.assertFalse(res)

    @patch("mona_sdk.client.requests.request")
    def test_export_with_exception(self, mock_request):
        """
        Asserts an export() call with wrong parameters causes
        the correct exception when RAISE_EXPORT_EXCEPTIONS = True.
        """
        test_mona_client = self._init_test_client(raise_export_exceptions=True)
        mock_request.return_value.ok = False
        mock_request.return_value.json.return_value = {
            "failed": 1,
            "failure_reasons": {},
        }

        with self.assertRaises(MonaExportException):
            # Test illegal export_timestamp type (can be a string describing a
            # number, but must be of length 10/13).
            test_mona_client.export(
                MonaSingleMessage(
                    message={"a": "some data"},
                    contextClass="TEST_CONTEXT_CLASS",
                    exportTimestamp="12345678",
                )
            )

    @patch("mona_sdk.client.requests.request")
    def _assert_batch_return_values(
        self, events, expected_total, expected_sent, expected_failed, mock_request
    ):
        """
        :param events: An iterable of events to batch-send.
        :param expected_total: The amount of events in events.
        :param expected_sent: The mount of events with correct content/structure.
        :param expected_failed: The amount of events with incorrect content/structure.
        """
        test_mona_client = self._init_test_client()

        mock_request.return_value.ok = not (expected_failed > 0)
        mock_request.return_value.json.return_value = {
            "failed": expected_failed,
            "failure_reasons": {},
        }

        res = test_mona_client.export_batch(events)
        self.assertEqual(res["total"], expected_total)
        self.assertEqual(res["sent"], expected_sent)
        self.assertEqual(res["failed"], expected_failed)

        # Assert export_batch raise an exception when raise_export_exceptions is true.
        test_mona_client = self._init_test_client(raise_export_exceptions=True)
        if expected_failed > 0:
            with self.assertRaises(MonaExportException):
                test_mona_client.export_batch(events)

    def test_export_batch(self):
        """
        Asserts a Client.export_batch() call with correct/incorrect
        messages structures replays with the corresponding result.
        """
        good_event = MonaSingleMessage(
            message={"a": "some data"}, contextClass="TEST_CONTEXT_CLASS"
        )
        empty_message_event = MonaSingleMessage(
            message=None,
            contextClass="TEST_CONTEXT_CLASS",
            contextId="TEST_CONTEXT_ID",
        )
        wrong_export_timestamp_type_event = MonaSingleMessage(
            message={"a": "some data"},
            contextClass="TEST_CONTEXT_CLASS",
            # When provided as a number, export_timestamp must have 10/13 digits
            # (seconds/ms since epoch).
            exportTimestamp=123456789,
        )
        wrong_export_timestamp_string_event = MonaSingleMessage(
            message={"a": "some data"},
            contextClass="TEST_CONTEXT_CLASS",
            exportTimestamp="this is not a timestamp",
        )
        wrong_context_class_event = MonaSingleMessage(
            message={"a": "some data"},
            # contextClass cannot end with "."
            contextClass="A.",
            # exportTimestamp can also be an ISO-format date (str).
            exportTimestamp=datetime.now().isoformat(),
        )
        self._assert_batch_return_values(
            [
                empty_message_event,
                wrong_export_timestamp_type_event,
                wrong_export_timestamp_string_event,
                wrong_context_class_event,
                good_event,
            ],
            5,
            1,
            4,
        )

    @staticmethod
    def _mock_request_generator_with_bad_response():
        return "Bad response"

    def test_get_auth_response_with_retries(self):
        num_of_retries = 5
        response = _get_auth_response_with_retries(
            lambda: self._mock_request_generator_with_bad_response(),
            num_of_retries=num_of_retries,
            auth_wait_time_sec=0,
        )
        response_dict = response.json()
        self.assertEqual(
            response_dict["errors"][1], f"Number of retries: {num_of_retries}"
        )


if __name__ == "__main__":
    unittest.main()
