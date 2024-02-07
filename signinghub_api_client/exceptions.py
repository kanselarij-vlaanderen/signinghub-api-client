import requests


class SigningHubException(Exception):
    def __init__(self, response):
        super().__init__(response)
        self.response = response
        self._response_truncated = False
        self._print_fields = {}

        try:
            data = response.json()
            if "Message" in data:
                self.error_description = data["Message"]
                self._print_fields["error description"] = self.error_description
        except requests.exceptions.JSONDecodeError:
            pass
        # Truncate the response text to 100K characters
        # to prevent huge responses from overloading the service
        max_body_length = 10000
        self._response_text = response.text[:max_body_length]
        if len(response.text) > max_body_length:
            self._response_truncated = True

    def __str__(self):
        class_name = type(self).__name__
        return """{class_name}
{fields}
response text{truncated}: {response_text}""".format(
            class_name=class_name,
            fields="\n".join([f"{k}: {v}" for k, v in self._print_fields.items()]),
            truncated=" (truncated)" if self._response_truncated else "",
            response_text=self._response_text,
        )


class AuthenticationException(SigningHubException):
    def __init__(self, response):
        super().__init__(response)
        try:
            data = response.json()
            self.error_id = data["error"] if "error" in data else None
            if "error" in data:
                self.error_id = data["error"]
                self._print_fields["error id"] = self.error_id
            if "error_description" in data:
                self.error_description = data["error_description"]
                self._print_fields["error description"] = self.error_description
        except requests.exceptions.JSONDecodeError:
            pass
        self.x_headers = {
            k: v for k, v in self.response.headers.items() if k.startswith("x-")
        }
        self._print_fields["x- headers"] = self.x_headers


class UnauthenticatedException(SigningHubException):
    pass
