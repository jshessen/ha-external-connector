"""AWS Trigger Service Module.

Service for managing AWS triggers including EventBridge rules and
API Gateway integrations.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from botocore.exceptions import ClientError

from .base import AWSServiceResponse, BaseAWSService
from .models import TriggerResourceSpec


class TriggerService(BaseAWSService):
    """Service for managing AWS triggers (EventBridge, API Gateway, etc.)."""

    async def create_or_update(self, spec: TriggerResourceSpec) -> AWSServiceResponse:
        """Create or update trigger."""
        try:
            if spec.trigger_type == "eventbridge":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._manage_eventbridge_rule, spec
                )
            if spec.trigger_type == "apigateway":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._manage_api_gateway_trigger, spec
                )
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported trigger type: {spec.trigger_type}"],
            )
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Trigger management failed: {str(e)}"]
            )

    def _manage_eventbridge_rule(self, spec: TriggerResourceSpec) -> AWSServiceResponse:
        """Manage EventBridge rule and target."""
        events_client = self._get_boto3_client("events")
        lambda_client = self._get_boto3_client("lambda")

        try:
            # Create or update EventBridge rule
            rule_params: dict[str, Any] = {
                "Name": spec.name,
                "State": "ENABLED",
            }

            if spec.description:
                rule_params["Description"] = spec.description

            if spec.event_pattern:
                rule_params["EventPattern"] = json.dumps(spec.event_pattern)
            elif spec.schedule_expression:
                rule_params["ScheduleExpression"] = spec.schedule_expression
            else:
                return AWSServiceResponse(
                    status="error",
                    errors=[
                        "EventBridge rule requires either event_pattern "
                        "or schedule_expression"
                    ],
                )

            if spec.event_bus_name:
                rule_params["EventBusName"] = spec.event_bus_name

            if spec.tags:
                rule_params["Tags"] = [
                    {"Key": k, "Value": v} for k, v in spec.tags.items()
                ]

            events_client.put_rule(**rule_params)

            # Add Lambda function as target
            target_params = {
                "Rule": spec.name,
                "Targets": [
                    {
                        "Id": "1",
                        "Arn": spec.target_function_arn,
                    }
                ],
            }

            if spec.event_bus_name:
                target_params["EventBusName"] = spec.event_bus_name

            events_client.put_targets(**target_params)

            # Add permission for EventBridge to invoke Lambda
            function_name = spec.target_function_arn.split(":")[-1]
            statement_id = f"eventbridge-{spec.name}"

            try:
                lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=statement_id,
                    Action="lambda:InvokeFunction",
                    Principal="events.amazonaws.com",
                    SourceArn=f"arn:aws:events:{self.region}:{self._get_account_id()}:rule/{spec.name}",
                )
            except ClientError as e:
                error_response = e.response.get("Error", {})
                if error_response.get("Code") != "ResourceConflictException":
                    raise

            return AWSServiceResponse(
                status="success",
                resource={
                    "rule_name": spec.name,
                    "rule_arn": (
                        f"arn:aws:events:{self.region}:"
                        f"{self._get_account_id()}:rule/{spec.name}"
                    ),
                    "target_function": spec.target_function_arn,
                    "operation": "created/updated",
                },
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS EventBridge error ({error_code}): {error_message}"],
            )

    def _manage_api_gateway_trigger(
        self, spec: TriggerResourceSpec
    ) -> AWSServiceResponse:
        """Manage API Gateway trigger (simplified integration)."""
        # Note: This is a simplified implementation for basic API Gateway integration
        # Full API Gateway management would require more comprehensive resource handling

        # Remove the unused assignment - API Gateway integration would require it
        # apigateway_client = self._get_boto3_client("apigateway")
        lambda_client = self._get_boto3_client("lambda")

        try:
            # Basic validation
            if not spec.api_id or not spec.resource_path or not spec.http_method:
                return AWSServiceResponse(
                    status="error",
                    errors=[
                        "API Gateway trigger requires api_id, "
                        "resource_path, and http_method"
                    ],
                )

            # Add permission for API Gateway to invoke Lambda
            function_name = spec.target_function_arn.split(":")[-1]
            statement_id = f"apigateway-{spec.api_id}-{spec.name}"
            # Create API Gateway execute ARN for Lambda permission
            account_id = self._get_account_id()
            source_arn = (
                f"arn:aws:execute-api:{self.region}:{account_id}:"
                f"{spec.api_id}/*/{spec.http_method}{spec.resource_path}"
            )

            try:
                lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=statement_id,
                    Action="lambda:InvokeFunction",
                    Principal="apigateway.amazonaws.com",
                    SourceArn=source_arn,
                )
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code != "ResourceConflictException":
                    raise

            return AWSServiceResponse(
                status="success",
                resource={
                    "trigger_name": spec.name,
                    "api_id": spec.api_id,
                    "resource_path": spec.resource_path,
                    "http_method": spec.http_method,
                    "target_function": spec.target_function_arn,
                    "operation": "permission_granted",
                    "note": (
                        "Basic API Gateway permission added - "
                        "full integration setup requires additional configuration"
                    ),
                },
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS API Gateway error ({error_code}): {error_message}"],
            )

    def _get_account_id(self) -> str:
        """Get AWS account ID."""
        sts_client = self._get_boto3_client("sts")
        return str(sts_client.get_caller_identity()["Account"])

    async def read(
        self, trigger_id: str, trigger_type: str = "eventbridge"
    ) -> AWSServiceResponse:
        """Read trigger configuration."""
        try:
            if trigger_type == "eventbridge":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._get_eventbridge_rule, trigger_id
                )
            if trigger_type == "apigateway":
                return AWSServiceResponse(
                    status="info",
                    resource={
                        "message": (
                            "API Gateway trigger reading requires "
                            "specific API ID and resource details"
                        )
                    },
                )
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported trigger type for read: {trigger_type}"],
            )
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Trigger read failed: {str(e)}"]
            )

    def _get_eventbridge_rule(self, rule_name: str) -> AWSServiceResponse:
        """Get EventBridge rule details."""
        events_client = self._get_boto3_client("events")

        try:
            # Get rule details
            rule_response = events_client.describe_rule(Name=rule_name)

            # Get targets
            targets_response = events_client.list_targets_by_rule(Rule=rule_name)

            rule_data = {
                "name": rule_response["Name"],
                "arn": rule_response["Arn"],
                "description": rule_response.get("Description", ""),
                "state": rule_response["State"],
                "schedule_expression": rule_response.get("ScheduleExpression"),
                "event_pattern": rule_response.get("EventPattern"),
                "event_bus_name": rule_response.get("EventBusName"),
                "targets": [
                    {
                        "id": target["Id"],
                        "arn": target["Arn"],
                    }
                    for target in targets_response.get("Targets", [])
                ],
            }

            return AWSServiceResponse(status="success", resource=rule_data)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                return AWSServiceResponse(
                    status="not_found",
                    errors=[f"EventBridge rule '{rule_name}' not found"],
                )

            error_message = e.response.get("Error", {}).get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS EventBridge error ({error_code}): {error_message}"],
            )

    async def delete(
        self, trigger_id: str, trigger_type: str = "eventbridge"
    ) -> AWSServiceResponse:
        """Delete trigger."""
        try:
            if trigger_type == "eventbridge":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._delete_eventbridge_rule, trigger_id
                )
            if trigger_type == "apigateway":
                return AWSServiceResponse(
                    status="info",
                    resource={
                        "message": (
                            "API Gateway trigger deletion requires "
                            "manual removal of integrations"
                        )
                    },
                )
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported trigger type for delete: {trigger_type}"],
            )
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Trigger deletion failed: {str(e)}"]
            )

    def _delete_eventbridge_rule(self, rule_name: str) -> AWSServiceResponse:
        """Delete EventBridge rule and clean up targets."""
        events_client = self._get_boto3_client("events")

        try:
            # Remove all targets from the rule first
            targets_response = events_client.list_targets_by_rule(Rule=rule_name)
            if targets_response.get("Targets"):
                target_ids = [target["Id"] for target in targets_response["Targets"]]
                events_client.remove_targets(Rule=rule_name, Ids=target_ids)

            # Delete the rule
            events_client.delete_rule(Name=rule_name)

            return AWSServiceResponse(
                status="success",
                resource={
                    "rule_name": rule_name,
                    "operation": "deleted",
                    "targets_removed": len(targets_response.get("Targets", [])),
                },
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                return AWSServiceResponse(
                    status="not_found",
                    errors=[f"EventBridge rule '{rule_name}' not found"],
                )

            error_message = e.response.get("Error", {}).get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS EventBridge error ({error_code}): {error_message}"],
            )

    async def list_triggers(
        self, trigger_type: str = "eventbridge"
    ) -> AWSServiceResponse:
        """List triggers."""
        try:
            if trigger_type == "eventbridge":
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._list_eventbridge_rules
                )
            if trigger_type == "apigateway":
                return AWSServiceResponse(
                    status="info",
                    resource={
                        "message": (
                            "API Gateway trigger listing requires "
                            "specific API management"
                        )
                    },
                )
            return AWSServiceResponse(
                status="error",
                errors=[f"Unsupported trigger type for list: {trigger_type}"],
            )
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Trigger listing failed: {str(e)}"]
            )

    def _list_eventbridge_rules(self) -> AWSServiceResponse:
        """List all EventBridge rules."""
        events_client = self._get_boto3_client("events")

        try:
            response = events_client.list_rules()
            rules: list[dict[str, Any]] = []

            for rule in response.get("Rules", []):
                rules.append(
                    {
                        "name": rule["Name"],
                        "arn": rule["Arn"],
                        "description": rule.get("Description", ""),
                        "state": rule["State"],
                        "schedule_expression": rule.get("ScheduleExpression"),
                        "event_pattern": rule.get("EventPattern"),
                        "event_bus_name": rule.get("EventBusName", "default"),
                    }
                )

            return AWSServiceResponse(
                status="success", resource={"rules": rules, "count": len(rules)}
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS EventBridge error ({error_code}): {error_message}"],
            )
