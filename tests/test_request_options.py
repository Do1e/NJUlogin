import unittest
from unittest.mock import patch

import requests

from NJUlogin import baseLogin


class RequestOptionsTests(unittest.TestCase):
    def setUp(self):
        self.login = baseLogin(timeout=5)
        self.login.session.trust_env = False
        self.addCleanup(self.login.session.close)
        self.url = "https://example.com/resource"
        self.response = requests.Response()
        self.response.status_code = 200
        self.response.url = self.url

    def request(self, method, **kwargs):
        if method == "post":
            return self.login.post(self.url, data={"key": "value"}, **kwargs)
        return self.login.get(self.url, **kwargs)

    def test_default_options(self):
        for method in ("get", "post"):
            with self.subTest(method=method):
                with patch.object(self.login.session, "send", return_value=self.response) as send:
                    self.assertIs(self.request(method), self.response)
                self.assertEqual(send.call_args.kwargs["timeout"], 5)
                self.assertIs(send.call_args.kwargs["verify"], False)
                if method == "post":
                    self.assertEqual(send.call_args.args[0].body, "key=value")

    def test_timeout_overrides(self):
        for method in ("get", "post"):
            for timeout in (10, (1, 7), None):
                with self.subTest(method=method, timeout=timeout):
                    with patch.object(
                        self.login.session, "send", return_value=self.response
                    ) as send:
                        self.assertIs(self.request(method, timeout=timeout), self.response)
                    self.assertEqual(send.call_args.kwargs["timeout"], timeout)
                    self.assertEqual(self.login.timeout, 5)

    def test_verify_overrides(self):
        for method in ("get", "post"):
            for verify in (True, False, "/tmp/custom-ca.pem"):
                with self.subTest(method=method, verify=verify):
                    with patch.object(
                        self.login.session, "send", return_value=self.response
                    ) as send:
                        self.assertIs(self.request(method, verify=verify), self.response)
                    self.assertEqual(send.call_args.kwargs["verify"], verify)

    def test_combined_options_and_passthrough(self):
        for method in ("get", "post"):
            with self.subTest(method=method):
                with patch.object(self.login.session, "send", return_value=self.response) as send:
                    self.request(
                        method,
                        timeout=10,
                        verify=True,
                        params={"page": 2},
                        headers={"X-Test": "value"},
                        allow_redirects=False,
                    )
                self.assertEqual(send.call_args.kwargs["timeout"], 10)
                self.assertIs(send.call_args.kwargs["verify"], True)
                self.assertIs(send.call_args.kwargs["allow_redirects"], False)
                request = send.call_args.args[0]
                self.assertEqual(request.url, self.url + "?page=2")
                self.assertEqual(request.headers["X-Test"], "value")

    def test_network_error_translation(self):
        for method in ("get", "post"):
            for source, expected in (
                (requests.exceptions.Timeout, TimeoutError),
                (requests.exceptions.ConnectionError, ConnectionError),
            ):
                with self.subTest(method=method, error=source.__name__):
                    with patch.object(self.login.session, "send", side_effect=source):
                        with self.assertRaises(expected) as error:
                            self.request(method)
                    self.assertIn(self.url, str(error.exception))


if __name__ == "__main__":
    unittest.main()
