# GdsAwsClient
# Manage sts assume-role calls and temporary credentials
import boto3
import os
import re
from datetime import datetime


class GdsAwsClient:

    # initialise empty dictionaries for clients and assume role sessions
    resources = dict()
    clients = dict()
    sessions = dict()

    resource_type = "AWS::*::*"
    annotation = ""

    def __init__(self, app=None):
        self.app = app
        self.chain = {}
        # self.get_chain_role_params()

    def get_chain_role_params(self):
        """
        Retrieve the secrets from SSM.
        """
        if self.chain == {}:
            # Only get the SSM params if they're not
            # already populated into self.chain
            params = {
                "/csw/chain/account": "account",
                "/csw/chain/chain_role": "chain_role",
                "/csw/chain/target_role": "target_role",
            }

            # Get list of SSM parameter names from dict
            param_list = list(params.keys())

            ssm = boto3.client("ssm")

            # Get all listed parameters in one API call
            response = ssm.get_parameters(Names=param_list, WithDecryption=True)

            for item in response["Parameters"]:
                param_name = params[item["Name"]]
                param_value = item["Value"]
                self.chain[param_name] = param_value

        return self.chain

    def to_camel_case(self, source_string, capitalize_first=True):

        components = re.sub(r"([a-z])([A-Z])", r"\1 \2", source_string).replace("_", " ").split(" ")
        # We capitalize the first letter of each component except the first one
        # with the 'title' method and join them together.
        for i,comp in enumerate(components):
            comp = comp.lower()
            if (i > 0) or (capitalize_first):
                comp = comp.title()
            components[i] = comp

        return "".join(components)

    # store temporary credentials from sts-assume-roles
    # session names are based on the account and role
    # {account-number}-{role-name}
    # eg: 779799343306-AdminRole
    def get_session_name(self, account, role=""):
        # Force account to be a 12 character zero padded string
        if account != "default":
            account = str(account).rjust(12, "0")
        if role == "":
            session_name = account
        else:
            session_name = f"{account}-{role}"
        return session_name

    # create clients once and reuse - store by client name
    # which encompasses the account, role and service
    # {account-number}-{role-name}-{region}-{service}
    # eg: 779799343306-AdminRole-eu-west-2-s3
    def get_client_name(self, service_name, session_name="default", region="eu-west-1"):
        return f"{session_name}-{region}-{service_name}"

    # gets a boto3.client class for the given service, account and role
    # if the client has already been defined in self.clients it is
    # reused instead of creating a new instance
    def get_boto3_client(self, service_name, account="default", role="", region=None):

        session_name = self.get_session_name(account, role)
        client_name = self.get_client_name(service_name, session_name, region)

        if client_name not in self.clients:

            if session_name == "default":
                client = self.get_default_client(service_name, region)

            else:
                client = self.get_assumed_client(service_name, account, role, region)

        else:
            client = self.clients[client_name]

        return client

    # gets a boto3.client with the default credentials
    def get_default_client(self, service_name, region=None):

        client_name = self.get_client_name(service_name, "default", region)

        # self.clients[client_name] = boto3.client(service_name) #, **creds)
        self.clients[client_name] = boto3.client(
            service_name,
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=os.environ["AWS_SESSION_TOKEN"],
            region_name=region,
        )
        return self.clients[client_name]

    def get_default_session(self):
        session = {
            "AccessKeyId": os.environ["AWS_ACCESS_KEY_ID"],
            "SecretAccessKey": os.environ["AWS_SECRET_ACCESS_KEY"],
            "SessionToken": os.environ["AWS_SESSION_TOKEN"]
        }
        return session

    # gets a boto3.client with the temporary session credentials
    # resulting from sts assume-role command
    def get_assumed_client(self, service_name, account="default", role="", region=None):

        session_name = self.get_session_name(account, role)
        client_name = self.get_client_name(service_name, session_name)

        session = self.get_session(account, role)
        self.clients[client_name] = boto3.client(
            service_name,
            aws_access_key_id=session["AccessKeyId"],
            aws_secret_access_key=session["SecretAccessKey"],
            aws_session_token=session["SessionToken"],
            region_name=region,
        )

        return self.clients[client_name]

    def get_boto3_session_client(self, service_name, session, region=None):

        client = boto3.client(
            service_name,
            aws_access_key_id=session["AccessKeyId"],
            aws_secret_access_key=session["SecretAccessKey"],
            aws_session_token=session["SessionToken"],
            region_name=region,
        )

        return client

    def get_boto3_resource(self, resource_name):

        if resource_name not in self.resources:
            self.resources[resource_name] = boto3.resource(resource_name)

        return self.resources[resource_name]

    # issue the sts assume-role command and store the returned credentials
    def assume_role(
        self, account, role, session=None, is_lambda=True, email="", token=""
    ):

        """
        Example response
        {
            'Credentials': {
                'AccessKeyId': 'string',
                'SecretAccessKey': 'string',
                'SessionToken': 'string',
                'Expiration': datetime(2015, 1, 1)
            },
            'AssumedRoleUser': {
                'AssumedRoleId': 'string',
                'Arn': 'string'
            },
            'PackedPolicySize': 123
        }
        """
        try:
            # force account to be 12 character string with leading zeros.
            if account != "default":
                account = str(account).rjust(12, "0")
            self.app.log.debug(f"Assuming to account: {account} with role: {role}")

            if session is None:
                sts = self.get_boto3_client("sts")
            else:
                sts = self.get_boto3_session_client("sts", session)

            role_arn = f"arn:aws:iam::{account}:role/{role}"
            print(f"Assume role: {role_arn}")

            session_name = self.get_session_name(account, role)

            # if in a lambda context the right to assume the role
            # is granted to the lambda function so no further
            # authentication is required
            if is_lambda:
                assumed_credentials = sts.assume_role(
                    RoleSessionName=session_name, RoleArn=role_arn
                )

            # in a command line context the MFA serial and token
            # are used to authenticate the user credentials
            else:
                mfa_serial = f"arn:aws:iam::622626885786:mfa/{email}"
                assumed_credentials = sts.assume_role(
                    RoleSessionName=session_name,
                    RoleArn=role_arn,
                    SerialNumber=mfa_serial,
                    TokenCode=token,
                )

            role_assumed = "Credentials" in assumed_credentials.keys()

            if role_assumed:
                expiry = assumed_credentials["Credentials"]["Expiration"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                self.app.log.debug("Session expiry: " + expiry)
                # self.app.log.debug('Time now: ' + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
                self.sessions[session_name] = assumed_credentials["Credentials"]
            else:
                raise Exception("Assume role failed")

        except Exception as exception:
            print(exception)
            role_assumed = False

        return role_assumed

    def get_caller_details(self, session=None):
        """
        Get the role and account id assumed by the current session credentials
        :param session:
        :return:
        """
        caller_details = None
        try:
            if session is None:
                sts = boto3.client("sts")
            else:
                sts = boto3.client(
                    "sts",
                    aws_access_key_id=session["AccessKeyId"],
                    aws_secret_access_key=session["SecretAccessKey"],
                    aws_session_token=session["SessionToken"],
                )

            caller_details = sts.get_caller_identity()
        except Exception as err:
            self.app.log.error("Failed to get caller details: " + str(err))
            pass

        return caller_details

    # get_session returns the existing session if it already exists
    # or assumes the role and returns the new session if it doesn't
    def get_session(self, account="default", role="", session=None):

        try:
            session_name = self.get_session_name(account, role)
            valid = False

            if session_name in self.sessions.keys():
                session = self.sessions[session_name]
                valid = True

                expiry = session["Expiration"].strftime("%Y-%m-%d %H:%M:%S")
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                if expiry < now:
                    self.sessions[session_name] = None
                    valid = False

            if not valid:

                assumed = self.assume_role(account, role, session)
                if not assumed:
                    raise Exception("Assume role failed")

            session = self.sessions[session_name]

        except Exception as exception:
            self.app.log.error(str(exception))
            session = None

        return session

    def assume_chained_role(self, target_account):
        """
        Assumed the target account:role by first assuming
        a chain account:role and only return true if both
        assumes complete successfully
        return: bool
        """
        assumed = False
        chain = self.get_chain_role_params()
        try:
            chain_assumed = self.assume_role(chain["account"], chain["chain_role"])
            if chain_assumed:
                chain_session = self.get_session(chain["account"], chain["chain_role"])
                assumed = self.assume_role(
                    target_account, chain["target_role"], session=chain_session
                )
        except Exception:
            self.app.log.error(self.app.utilities.get_typed_exception())

        return assumed

    def get_chained_session(self, target_account):
        """
        Assumed the target account:role by first assuming
        a chain account:role and only return true if both
        assumes complete successfully
        return: session dict|None
        """
        target_session = None
        try:
            chain = self.get_chain_role_params()
            chain_assumed = self.assume_role(chain["account"], chain["chain_role"])
            if chain_assumed:
                chain_session = self.get_session(chain["account"], chain["chain_role"])
                target_session = self.get_session(
                    target_account, chain["target_role"], session=chain_session
                )
        except Exception:
            self.app.log.error(self.app.utilities.get_typed_exception())

        return target_session

    def parse_arn_components(self, arn):

        # arn:aws:[service]:[region]:[account]:[resource]
        component_values = arn.split(":")

        components = {
            "service": component_values[2],
            "region": component_values[3],
            "account": component_values[4],
            "resource": component_values[5]
        }

        return components

    def tag_list_to_dict(self, tags):
        tag_dict = {}
        for tag in tags:
            tag_dict[tag["Key"]] = tag["Value"]
        return tag_dict

