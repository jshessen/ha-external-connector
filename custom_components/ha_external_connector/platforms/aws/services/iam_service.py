"""AWS IAM Service Module.

Service for managing AWS IAM resources including roles, policies, and user management
with sophisticated error handling and validation patterns.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from botocore.exceptions import ClientError

from .base import AWSServiceResponse, BaseAWSService
from .models import IAMResourceSpec


class IAMService(BaseAWSService):
    """Service for managing AWS IAM resources.

    Provides comprehensive IAM management including roles, policies, and user management
    with sophisticated error handling and validation patterns.
    """

    def __init__(self, region: str = "us-east-1") -> None:
        super().__init__(region)
        self._boto3_clients: dict[str, Any] = {}

    def _get_boto3_client(self, service: str) -> Any:
        """Get or create a boto3 client for the specified service.

        Args:
            service: AWS service name

        Returns:
            Boto3 client instance
        """
        if service not in self._boto3_clients:
            self._boto3_clients[service] = super()._get_boto3_client(service)
        return self._boto3_clients[service]

    async def create_or_update(self, spec: IAMResourceSpec) -> AWSServiceResponse:
        """Create or update IAM resource.

        Args:
            spec: IAM resource specification

        Returns:
            Response containing resource status and details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._manage_iam_resource, spec
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )

    def _manage_iam_resource(self, spec: IAMResourceSpec) -> AWSServiceResponse:
        """Manage IAM resource creation/update.

        Args:
            spec: IAM resource specification

        Returns:
            Resource management response
        """
        iam_client = self._get_boto3_client("iam")

        try:
            if spec.resource_type == "role":
                return self._manage_iam_role(iam_client, spec)
            if spec.resource_type == "policy":
                return self._manage_iam_policy(iam_client, spec)
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported resource type: {spec.resource_type}"],
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )

    def _manage_iam_role(
        self, iam_client: Any, spec: IAMResourceSpec
    ) -> AWSServiceResponse:
        """Manage IAM role creation/update.

        Args:
            iam_client: IAM client instance
            spec: IAM resource specification

        Returns:
            Role management response
        """
        role_name = spec.name

        try:
            # Check if role exists
            try:
                iam_client.get_role(RoleName=role_name)
                role_exists = True
            except ClientError as e:
                error_response = e.response.get("Error", {})
                if error_response.get("Code") == "NoSuchEntity":
                    role_exists = False
                else:
                    raise

            if role_exists:
                # Update existing role's trust policy if provided
                if spec.assume_role_policy:
                    iam_client.update_assume_role_policy(
                        RoleName=role_name,
                        PolicyDocument=json.dumps(spec.assume_role_policy),
                    )

                # Get updated role
                response = iam_client.get_role(RoleName=role_name)
                role_info = response["Role"]
            else:
                # Create new role
                if not spec.assume_role_policy:
                    return AWSServiceResponse(
                        status="error",
                        errors=["Assume role policy is required for new roles"],
                    )

                response = iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(spec.assume_role_policy),
                    Description=spec.description
                    or f"Role {role_name} managed by HA External Connector",
                )
                role_info = response["Role"]

            # Attach policy if provided
            if spec.policy_document:
                policy_name = f"{role_name}Policy"
                try:
                    # Try to create inline policy
                    iam_client.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(spec.policy_document),
                    )
                except ClientError as e:
                    # If policy already exists, update it
                    error_response = e.response.get("Error", {})
                    if error_response.get("Code") == "EntityAlreadyExists":
                        iam_client.put_role_policy(
                            RoleName=role_name,
                            PolicyName=policy_name,
                            PolicyDocument=json.dumps(spec.policy_document),
                        )
                    else:
                        raise

            return AWSServiceResponse(
                status="success",
                resource={
                    "role_name": role_info["RoleName"],
                    "role_arn": role_info["Arn"],
                    "role_id": role_info["RoleId"],
                    "created_date": role_info["CreateDate"].isoformat(),
                    "description": role_info.get("Description", ""),
                    "max_session_duration": role_info.get("MaxSessionDuration", 3600),
                    "path": role_info.get("Path", "/"),
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"Role management error ({error_code}): {error_message}"],
            )

    def _manage_iam_policy(
        self, iam_client: Any, spec: IAMResourceSpec
    ) -> AWSServiceResponse:
        """Manage IAM policy creation/update.

        Args:
            iam_client: IAM client instance
            spec: IAM resource specification

        Returns:
            Policy management response
        """
        policy_name = spec.name

        try:
            if not spec.policy_document:
                return AWSServiceResponse(
                    status="error",
                    errors=["Policy document is required for policy resources"],
                )

            # Check if managed policy exists
            account_id = self._get_account_id()
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

            try:
                iam_client.get_policy(PolicyArn=policy_arn)
                policy_exists = True
            except ClientError as e:
                error_response = e.response.get("Error", {})
                if error_response.get("Code") == "NoSuchEntity":
                    policy_exists = False
                else:
                    raise

            if policy_exists:
                # Create new policy version
                response = iam_client.create_policy_version(
                    PolicyArn=policy_arn,
                    PolicyDocument=json.dumps(spec.policy_document),
                    SetAsDefault=True,
                )
                version_id = response["PolicyVersion"]["VersionId"]

                # Get policy info
                policy_response = iam_client.get_policy(PolicyArn=policy_arn)
                policy_info = policy_response["Policy"]

                return AWSServiceResponse(
                    status="success",
                    resource={
                        "policy_name": policy_info["PolicyName"],
                        "policy_arn": policy_info["Arn"],
                        "policy_id": policy_info["PolicyId"],
                        "version_id": version_id,
                        "created_date": policy_info["CreateDate"].isoformat(),
                        "updated_date": policy_info["UpdateDate"].isoformat(),
                        "description": policy_info.get("Description", ""),
                    },
                )
            # Create new policy
            response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(spec.policy_document),
                Description=spec.description
                or f"Policy {policy_name} managed by HA External Connector",
            )
            policy_info = response["Policy"]

            return AWSServiceResponse(
                status="success",
                resource={
                    "policy_name": policy_info["PolicyName"],
                    "policy_arn": policy_info["Arn"],
                    "policy_id": policy_info["PolicyId"],
                    "version_id": "v1",
                    "created_date": policy_info["CreateDate"].isoformat(),
                    "description": policy_info.get("Description", ""),
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"Policy management error ({error_code}): {error_message}"],
            )

    def _get_account_id(self) -> str:
        """Get AWS account ID.

        Returns:
            AWS account ID
        """
        sts_client = self._get_boto3_client("sts")
        response = sts_client.get_caller_identity()
        return str(response["Account"])

    async def read(
        self, resource_name: str, resource_type: str = "role"
    ) -> AWSServiceResponse:
        """Read IAM resource.

        Args:
            resource_name: Name of the resource
            resource_type: Type of resource (role, policy)

        Returns:
            Response containing resource details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._get_iam_resource, resource_name, resource_type
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )

    def _get_iam_resource(
        self, resource_name: str, resource_type: str
    ) -> AWSServiceResponse:
        """Get IAM resource details.

        Args:
            resource_name: Name of the resource
            resource_type: Type of resource

        Returns:
            Resource details response
        """
        try:
            if resource_type == "role":
                return self._get_role_details(resource_name)
            if resource_type == "policy":
                return self._get_policy_details(resource_name)
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported resource type: {resource_type}"],
            )

        except ClientError as e:
            return self._handle_get_resource_error(e, resource_name, resource_type)

    def _get_role_details(self, resource_name: str) -> AWSServiceResponse:
        """Get IAM role details with policies.

        Args:
            resource_name: Name of the role

        Returns:
            Role details response
        """
        iam_client = self._get_boto3_client("iam")

        response = iam_client.get_role(RoleName=resource_name)
        role_info = response["Role"]

        # Get attached policies
        policies_response = iam_client.list_role_policies(RoleName=resource_name)
        inline_policies = policies_response["PolicyNames"]

        attached_response = iam_client.list_attached_role_policies(
            RoleName=resource_name
        )
        attached_policies = [
            p["PolicyArn"] for p in attached_response["AttachedPolicies"]
        ]

        return AWSServiceResponse(
            status="success",
            resource={
                "role_name": role_info["RoleName"],
                "role_arn": role_info["Arn"],
                "role_id": role_info["RoleId"],
                "created_date": role_info["CreateDate"].isoformat(),
                "description": role_info.get("Description", ""),
                "max_session_duration": role_info.get("MaxSessionDuration", 3600),
                "path": role_info.get("Path", "/"),
                "inline_policies": inline_policies,
                "attached_policies": attached_policies,
                "assume_role_policy": role_info.get("AssumeRolePolicyDocument", {}),
            },
        )

    def _get_policy_details(self, resource_name: str) -> AWSServiceResponse:
        """Get IAM policy details with document.

        Args:
            resource_name: Name of the policy

        Returns:
            Policy details response
        """
        iam_client = self._get_boto3_client("iam")

        account_id = self._get_account_id()
        policy_arn = f"arn:aws:iam::{account_id}:policy/{resource_name}"

        response = iam_client.get_policy(PolicyArn=policy_arn)
        policy_info = response["Policy"]

        # Get default policy version
        version_response = iam_client.get_policy_version(
            PolicyArn=policy_arn, VersionId=policy_info["DefaultVersionId"]
        )
        policy_document = version_response["PolicyVersion"]["Document"]

        return AWSServiceResponse(
            status="success",
            resource={
                "policy_name": policy_info["PolicyName"],
                "policy_arn": policy_info["Arn"],
                "policy_id": policy_info["PolicyId"],
                "default_version_id": policy_info["DefaultVersionId"],
                "created_date": policy_info["CreateDate"].isoformat(),
                "updated_date": policy_info["UpdateDate"].isoformat(),
                "description": policy_info.get("Description", ""),
                "attachment_count": policy_info.get("AttachmentCount", 0),
                "policy_document": policy_document,
            },
        )

    def _handle_get_resource_error(
        self, error: ClientError, resource_name: str, resource_type: str
    ) -> AWSServiceResponse:
        """Handle errors from getting IAM resources.

        Args:
            error: The ClientError that occurred
            resource_name: Name of the resource
            resource_type: Type of resource

        Returns:
            Error response
        """
        error_response = error.response.get("Error", {})
        error_code = error_response.get("Code", "Unknown")

        if error_code == "NoSuchEntity":
            return AWSServiceResponse(
                status="not_found",
                errors=[f"{resource_type.title()} not found: {resource_name}"],
            )
        error_message = error_response.get("Message", "Unknown error")
        return AWSServiceResponse(
            status="error",
            errors=[f"AWS IAM error ({error_code}): {error_message}"],
        )

    async def delete(
        self, resource_name: str, resource_type: str = "role"
    ) -> AWSServiceResponse:
        """Delete IAM resource.

        Args:
            resource_name: Name of the resource to delete
            resource_type: Type of resource (role, policy)

        Returns:
            Deletion response
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._delete_iam_resource, resource_name, resource_type
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Delete operation failed: {str(e)}"]
            )

    def _delete_iam_resource(
        self, resource_name: str, resource_type: str
    ) -> AWSServiceResponse:
        """Delete IAM resource.

        Args:
            resource_name: Name of the resource
            resource_type: Type of resource

        Returns:
            Deletion response
        """
        try:
            if resource_type == "role":
                return self._delete_role(resource_name)
            if resource_type == "policy":
                return self._delete_policy(resource_name)
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported resource type: {resource_type}"],
            )

        except ClientError as e:
            return self._handle_delete_resource_error(e, resource_name, resource_type)

    def _delete_role(self, resource_name: str) -> AWSServiceResponse:
        """Delete IAM role and its attached policies.

        Args:
            resource_name: Name of the role

        Returns:
            Deletion response
        """
        iam_client = self._get_boto3_client("iam")

        # Detach all managed policies
        attached_response = iam_client.list_attached_role_policies(
            RoleName=resource_name
        )
        for policy in attached_response["AttachedPolicies"]:
            iam_client.detach_role_policy(
                RoleName=resource_name, PolicyArn=policy["PolicyArn"]
            )

        # Delete all inline policies
        policies_response = iam_client.list_role_policies(RoleName=resource_name)
        for policy_name in policies_response["PolicyNames"]:
            iam_client.delete_role_policy(
                RoleName=resource_name, PolicyName=policy_name
            )

        # Delete role
        iam_client.delete_role(RoleName=resource_name)

        return AWSServiceResponse(
            status="success", resource={"deleted_role": resource_name}
        )

    def _delete_policy(self, resource_name: str) -> AWSServiceResponse:
        """Delete IAM policy and its versions.

        Args:
            resource_name: Name of the policy

        Returns:
            Deletion response
        """
        iam_client = self._get_boto3_client("iam")

        account_id = self._get_account_id()
        policy_arn = f"arn:aws:iam::{account_id}:policy/{resource_name}"

        # List and delete non-default policy versions
        versions_response = iam_client.list_policy_versions(PolicyArn=policy_arn)
        for version in versions_response["Versions"]:
            if not version["IsDefaultVersion"]:
                iam_client.delete_policy_version(
                    PolicyArn=policy_arn, VersionId=version["VersionId"]
                )

        # Delete policy
        iam_client.delete_policy(PolicyArn=policy_arn)

        return AWSServiceResponse(
            status="success",
            resource={
                "deleted_policy": resource_name,
                "policy_arn": policy_arn,
            },
        )

    def _handle_delete_resource_error(
        self, error: ClientError, resource_name: str, resource_type: str
    ) -> AWSServiceResponse:
        """Handle errors from deleting IAM resources.

        Args:
            error: The ClientError that occurred
            resource_name: Name of the resource
            resource_type: Type of resource

        Returns:
            Error response
        """
        error_response = error.response.get("Error", {})
        error_code = error_response.get("Code", "Unknown")

        if error_code == "NoSuchEntity":
            return AWSServiceResponse(
                status="not_found",
                errors=[f"{resource_type.title()} not found: {resource_name}"],
            )
        error_message = error_response.get("Message", "Unknown error")
        return AWSServiceResponse(
            status="error",
            errors=[f"AWS IAM error ({error_code}): {error_message}"],
        )

    async def list_roles(self) -> AWSServiceResponse:
        """List IAM roles.

        Returns:
            Response containing list of roles
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._list_iam_roles
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )

    def _list_iam_roles(self) -> AWSServiceResponse:
        """List IAM roles.

        Returns:
            List of roles response
        """
        iam_client = self._get_boto3_client("iam")

        try:
            response = iam_client.list_roles()
            roles: list[dict[str, Any]] = []

            for role in response["Roles"]:
                roles.append(
                    {
                        "role_name": role["RoleName"],
                        "role_arn": role["Arn"],
                        "role_id": role["RoleId"],
                        "created_date": role["CreateDate"].isoformat(),
                        "description": role.get("Description", ""),
                        "max_session_duration": role.get("MaxSessionDuration", 3600),
                        "path": role.get("Path", "/"),
                    }
                )

            return AWSServiceResponse(
                status="success", resource={"roles": roles, "count": len(roles)}
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )

    async def list_policies(self) -> AWSServiceResponse:
        """List IAM managed policies.

        Returns:
            Response containing list of policies
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._list_iam_policies
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )

    def _list_iam_policies(self) -> AWSServiceResponse:
        """List IAM managed policies.

        Returns:
            List of policies response
        """
        iam_client = self._get_boto3_client("iam")

        try:
            # List only customer managed policies (not AWS managed)
            response = iam_client.list_policies(Scope="Local")
            policies: list[dict[str, Any]] = []

            for policy in response["Policies"]:
                policies.append(
                    {
                        "policy_name": policy["PolicyName"],
                        "policy_arn": policy["Arn"],
                        "policy_id": policy["PolicyId"],
                        "default_version_id": policy["DefaultVersionId"],
                        "created_date": policy["CreateDate"].isoformat(),
                        "updated_date": policy["UpdateDate"].isoformat(),
                        "description": policy.get("Description", ""),
                        "attachment_count": policy.get("AttachmentCount", 0),
                    }
                )

            return AWSServiceResponse(
                status="success",
                resource={"policies": policies, "count": len(policies)},
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS IAM error ({error_code}): {error_message}"],
            )
