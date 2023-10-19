import requests

class SigningHubException(Exception):
    def __init__(self, response):
        super().__init__(response)
        self.response = response
        try:
            data = response.json()
            if "Message" in data:
                self.error_description = data["Message"]
        except requests.exceptions.JSONDecodeError:
            # Truncate the response text to 100K characters
            # to prevent huge responses from overloading the service
            self.error_description = response.text[:100000]

    def __str__(self):
        return """SigningHubException:
error description: {error_description}""".format(
    error_description=self.error_description)


class AuthenticationException(SigningHubException):
    def __init__(self, response):
        super().__init__(response)
        data = response.json()
        self.error_id = data["error"]
        self.error_description = data["error_description"] if "error_description" in data else None
        self.x_headers = {k: v for k, v in self.response.headers.items() if k.startswith("x-")}

    def __str__(self):
        return """SigningHub AuthenticationException:
error: "{error_id}"
error description: {error_description}
x- headers: {x_headers}""".format(
        error_id=self.error_id,
        error_description=self.error_description,
        x_headers=self.x_headers)


class UnauthenticatedException(SigningHubException):
    def __str__(self):
        return """SigningHub UnauthenticatedException:
error description: {error_description}""".format(
    error_description=self.error_description)
