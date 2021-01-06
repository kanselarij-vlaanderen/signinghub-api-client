from datetime import datetime, timedelta, timezone
from requests_toolbelt.sessions import BaseUrlSession
from .exceptions import SigningHubException, AuthenticationException, UnauthenticatedException

class SigningHubSession(BaseUrlSession):
    def __init__(self, base_url):
        self.base_url = base_url
        self.last_successful_auth_time = None
        self.access_token_expiry_time = None
        self.refresh_token = None
        super().__init__(base_url)
        self.headers["Accept"] = "application/json"

    @property
    def token_expired(self):
        return datetime.now(timezone.utc) > (self.last_successful_auth_time + self.access_token_expiry_time)

    @property
    def access_token(self):
        return self.headers["Authorization"].replace("Bearer ", "")

    @access_token.setter
    def access_token(self, token):
        if token is not None:
            self.headers["Authorization"] = "Bearer {}".format(token)
        else:
            del self.headers["Authorization"]

    @access_token.deleter
    def access_token(self):
        del self.headers["Authorization"]

    def request(self, method, url, *args, **kwargs):
        response = super().request(method, url, *args, **kwargs)
        if response.status_code == 200:
            if "application/json" in response.headers["Content-Type"]: # TODO: Proper mime-type parsing
                return response.json()
            if "application/octet-stream" in response.headers["Content-Type"]:
                return response.content # Bytes
            return response
        if response.status_code == 401:
            raise UnauthenticatedException(response)
        raise SigningHubException(response)

    ############################################################################
    # AUTHENTICATION
    ############################################################################
    def authenticate(self, client_id, client_secret, grant_type="password", username=None, password=None, scope=None):
        """
        username and password are optional when a previous authentication provided a "refresh_token"
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1010
        """
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": grant_type
        }
        if scope is not None:
            data["scope"] = scope

        if (username is None) and (password is None) and (self.refresh_token is not None):
            data["refresh_token"] = self.refresh_token
        else:
            data["username"] = username
            data["password"] = password
        response = super().request("POST", "authenticate", data=data)
        self.__process_authentication_response(response)

    def authenticate_sso(self, token, method):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1192
        """
        data = {
            "token": token,
            "method": method
        }
        response = super().request("POST", "authenticate/sso", json=data)
        self.__process_authentication_response(response)

    def __process_authentication_response(self, response):
        self.refresh_token = None
        if response.status_code == 200:
            self.last_successful_auth_time = datetime.now(timezone.utc)
            data = response.json()
            self.access_token = data["access_token"]
            self.access_token_expiry_time = timedelta(seconds=data["expires_in"])
            self.refresh_token = data["refresh_token"]
        else:
            raise AuthenticationException(response)

    def logout(self):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1161
        """
        data = self.post("logout")
        self.last_successful_auth_time = None
        self.access_token_expiry_time = None
        self.refresh_token = None
        self.access_token = None
        return data

    ############################################################################
    # PERSONAL SETTING
    ############################################################################
    def get_general_profile_information(self):
        """
        "Get General Profile Information"
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1104
        """
        return self.get("v4/settings/profile")


    ############################################################################
    # PACKAGE
    ############################################################################
    def add_package(self, data):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1020
        """
        return self.post("v4/packages", json=data)


    ############################################################################
    # DOCUMENT
    ############################################################################
    def upload_document(self, package_id, data, filename, source, convert_document=True):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1022
        """
        url = "v4/packages/{package_id}/documents".format(package_id=package_id)
        headers = {
            "x-file-name": filename,
            "x-convert-document": "true" if convert_document else "false",
            "x-source": source
        }
        # TODO: Are these headers added to the session headers?
        # TODO: Is mime-type automatically "application/octet-stream"?
        return self.post(url, data=data, headers=headers)

    def download_document(self, package_id, document_id):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1029
        """
        url = "v4/packages/{package_id}/documents/{document_id}".format(
            package_id=package_id, document_id=document_id)
        self.headers["Accept"] = "application/octet-stream"
        return self.get(url)

    def add_signature_field(self, package_id, document_id, data):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1069
        """
        url = "v4/packages/{package_id}/documents/{document_id}/fields/signature".format(
            package_id=package_id, document_id=document_id)
        return self.post(url, json=data)

    def get_document_fields(self, package_id, document_id, page_no=None):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1065
        """
        url = "v4/packages/{package_id}/documents/{document_id}/fields".format(
            package_id=package_id, document_id=document_id)
        if page_no is not None:
            url = url + "/{page_no:d}".format(page_no=page_no)
        self.headers["Content-Type"] = "application/json" # No content, but API doc specifies this
        return self.get(url)

    ############################################################################
    # WORKFLOW
    ############################################################################
    def get_workflow_details(self, package_id):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1042
        """
        url = "v4/packages/{package_id}/workflow".format(package_id=package_id)
        self.headers["Content-Type"] = "application/json" # No content, but API doc specifies this
        return self.get(url)

    def update_workflow_details(self, package_id, data):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1043
        """
        url = "v4/packages/{package_id}/workflow".format(package_id=package_id)
        return self.put(url, json=data)

    def add_users_to_workflow(self, package_id, data):
        """
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1047
        """
        url = "v4/packages/{package_id}/workflow/users".format(package_id=package_id)
        return self.post(url, json=data)

    def share_document_package(self, package_id):
        """
        "Send out the workflow"
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1025
        """
        url = "v4/packages/{package_id}/workflow".format(package_id=package_id)
        self.headers["Content-Type"] = "application/json" # No content, but API doc specifies this
        return self.post(url)

    def get_integration_link(self, package_id, data):
        """
        No real documentation page is available for this call.
        "Step 12 - Generate Integration URL for Encrypted Data (Coding)" of the following page has some useful info.
        https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1004
        """
        url = "v4/links/integration"
        data["package_id"] = package_id
        return self.post(url, json=data) # TODO: if API returns response with wrong content-type, this will fail.

