"""AWS CloudWatch Logs Service Module.

Service for managing AWS CloudWatch Logs with comprehensive log group management,
log stream operations, and sophisticated monitoring capabilities.
"""

from __future__ import annotations

import asyncio
from typing import Any

from botocore.exceptions import ClientError

from .base import AWSServiceResponse, BaseAWSService
from .models import LogQueryConfig, LogsResourceSpec


class LogsService(BaseAWSService):
    """Service for managing AWS CloudWatch Logs.

    Provides comprehensive log group management, log stream operations,
    and sophisticated monitoring capabilities with error handling patterns.
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

    async def create_or_update(self, spec: LogsResourceSpec) -> AWSServiceResponse:
        """Create or update CloudWatch log group.

        Args:
            spec: Logs resource specification

        Returns:
            Response containing log group status and details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._manage_log_group, spec
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Logs operation failed: {str(e)}"]
            )

    def _check_log_group_exists(
        self, logs_client, log_group_name: str
    ) -> tuple[bool, dict[str, Any] | None]:
        """Check if CloudWatch log group exists.

        Args:
            logs_client: CloudWatch Logs client instance
            log_group_name: Name of log group to check

        Returns:
            Tuple of (exists, existing_group_dict)
        """
        try:
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=log_group_name, limit=1
            )
            existing_groups = [
                lg
                for lg in response["logGroups"]
                if lg["logGroupName"] == log_group_name
            ]
            if existing_groups:
                return True, existing_groups[0]
            return False, None
        except ClientError:
            return False, None

    def _create_log_group_if_needed(
        self, logs_client, spec: LogsResourceSpec, log_group_exists: bool
    ) -> str:
        """Create log group if it doesn't exist.

        Args:
            logs_client: CloudWatch Logs client instance
            spec: Log group specification
            log_group_exists: Whether log group already exists

        Returns:
            Operation performed ("created" or "exists")
        """
        if log_group_exists:
            return "exists"

        create_params: dict[str, Any] = {"logGroupName": spec.log_group_name}

        if spec.kms_key_id:
            create_params["kmsKeyId"] = spec.kms_key_id

        if spec.tags:
            create_params["tags"] = spec.tags

        logs_client.create_log_group(**create_params)
        return "created"

    def _update_log_group_retention(
        self, logs_client, spec: LogsResourceSpec, existing_group: dict[str, Any] | None
    ) -> bool:
        """Update log group retention policy if needed.

        Args:
            logs_client: CloudWatch Logs client instance
            spec: Log group specification
            existing_group: Existing log group details

        Returns:
            Whether retention was updated
        """
        if not spec.retention_days:
            return False

        current_retention = (
            existing_group.get("retentionInDays") if existing_group else None
        )

        if current_retention == spec.retention_days:
            return False

        logs_client.put_retention_policy(
            logGroupName=spec.log_group_name,
            retentionInDays=spec.retention_days,
        )
        return True

    def _manage_log_group(self, spec: LogsResourceSpec) -> AWSServiceResponse:
        """Manage CloudWatch log group creation/update.

        Args:
            spec: Logs resource specification

        Returns:
            Log group management response
        """
        logs_client = self._get_boto3_client("logs")

        try:
            # Check if log group exists
            log_group_exists, existing_group = self._check_log_group_exists(
                logs_client, spec.log_group_name
            )

            # Create log group if needed
            operation = self._create_log_group_if_needed(
                logs_client, spec, log_group_exists
            )

            # Update retention policy if specified
            retention_updated = self._update_log_group_retention(
                logs_client, spec, existing_group
            )

            # Get updated log group details
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=spec.log_group_name, limit=1
            )
            log_group = next(
                (
                    lg
                    for lg in response["logGroups"]
                    if lg["logGroupName"] == spec.log_group_name
                ),
                None,
            )

            if not log_group:
                return AWSServiceResponse(
                    status="error",
                    errors=[f"Failed to retrieve log group: {spec.log_group_name}"],
                )

            return AWSServiceResponse(
                status="success",
                resource={
                    "log_group_name": log_group["logGroupName"],
                    "log_group_arn": log_group["arn"],
                    "creation_time": log_group["creationTime"],
                    "retention_days": log_group.get("retentionInDays"),
                    "metric_filter_count": log_group.get("metricFilterCount", 0),
                    "stored_bytes": log_group.get("storedBytes", 0),
                    "kms_key_id": log_group.get("kmsKeyId", ""),
                    "operation": operation,
                    "retention_updated": retention_updated,
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS CloudWatch Logs error ({error_code}): {error_message}"],
            )

    async def read(self, log_group_name: str) -> AWSServiceResponse:
        """Read CloudWatch log group details.

        Args:
            log_group_name: Name of the log group to read

        Returns:
            Response containing log group details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._get_log_group, log_group_name
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Read operation failed: {str(e)}"]
            )

    def _get_log_group(self, log_group_name: str) -> AWSServiceResponse:
        """Get CloudWatch log group details.

        Args:
            log_group_name: Name of the log group

        Returns:
            Log group details response
        """
        logs_client = self._get_boto3_client("logs")

        try:
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=log_group_name, limit=1
            )

            log_groups = [
                lg
                for lg in response["logGroups"]
                if lg["logGroupName"] == log_group_name
            ]

            if not log_groups:
                return AWSServiceResponse(
                    status="not_found",
                    errors=[f"Log group not found: {log_group_name}"],
                )

            log_group = log_groups[0]

            # Get log streams for additional information
            try:
                streams_response = logs_client.describe_log_streams(
                    logGroupName=log_group_name, orderBy="LastEventTime", limit=5
                )
                recent_streams: list[dict[str, Any]] = streams_response["logStreams"]
            except ClientError:
                recent_streams = []

            return AWSServiceResponse(
                status="success",
                resource={
                    "log_group_name": log_group["logGroupName"],
                    "log_group_arn": log_group["arn"],
                    "creation_time": log_group["creationTime"],
                    "retention_days": log_group.get("retentionInDays"),
                    "metric_filter_count": log_group.get("metricFilterCount", 0),
                    "stored_bytes": log_group.get("storedBytes", 0),
                    "kms_key_id": log_group.get("kmsKeyId", ""),
                    "recent_log_streams": [
                        {
                            "stream_name": stream["logStreamName"],
                            "creation_time": stream["creationTime"],
                            "last_event_time": stream.get("lastEventTime"),
                            "last_ingestion_time": stream.get("lastIngestionTime"),
                        }
                        for stream in recent_streams
                    ],
                    "stream_count": len(recent_streams),
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS CloudWatch Logs error ({error_code}): {error_message}"],
            )

    async def delete(self, log_group_name: str) -> AWSServiceResponse:
        """Delete CloudWatch log group.

        Args:
            log_group_name: Name of the log group to delete

        Returns:
            Deletion response
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._delete_log_group, log_group_name
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Delete operation failed: {str(e)}"]
            )

    def _delete_log_group(self, log_group_name: str) -> AWSServiceResponse:
        """Delete CloudWatch log group.

        Args:
            log_group_name: Name of the log group

        Returns:
            Deletion response
        """
        logs_client = self._get_boto3_client("logs")

        try:
            logs_client.delete_log_group(logGroupName=log_group_name)

            return AWSServiceResponse(
                status="success", resource={"deleted_log_group": log_group_name}
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            if error_response.get("Code") == "ResourceNotFoundException":
                return AWSServiceResponse(
                    status="not_found",
                    errors=[f"Log group not found: {log_group_name}"],
                )

            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS CloudWatch Logs error ({error_code}): {error_message}"],
            )

    async def list_log_groups(
        self, name_prefix: str | None = None
    ) -> AWSServiceResponse:
        """List CloudWatch log groups.

        Args:
            name_prefix: Optional name prefix to filter log groups

        Returns:
            Response containing list of log groups
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._list_log_groups, name_prefix
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"List operation failed: {str(e)}"]
            )

    def _list_log_groups(self, name_prefix: str | None) -> AWSServiceResponse:
        """List CloudWatch log groups.

        Args:
            name_prefix: Optional name prefix to filter log groups

        Returns:
            List of log groups response
        """
        logs_client = self._get_boto3_client("logs")

        try:
            describe_params = {}

            if name_prefix:
                describe_params["logGroupNamePrefix"] = name_prefix

            response = logs_client.describe_log_groups(**describe_params)
            log_groups: list[dict[str, Any]] = []

            for lg in response["logGroups"]:
                log_groups.append(
                    {
                        "log_group_name": lg["logGroupName"],
                        "log_group_arn": lg["arn"],
                        "creation_time": lg["creationTime"],
                        "retention_days": lg.get("retentionInDays"),
                        "metric_filter_count": lg.get("metricFilterCount", 0),
                        "stored_bytes": lg.get("storedBytes", 0),
                        "kms_key_id": lg.get("kmsKeyId", ""),
                    }
                )

            return AWSServiceResponse(
                status="success",
                resource={
                    "log_groups": log_groups,
                    "count": len(log_groups),
                    "name_prefix": name_prefix,
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS CloudWatch Logs error ({error_code}): {error_message}"],
            )

    async def get_log_events(self, config: LogQueryConfig) -> AWSServiceResponse:
        """Get log events from CloudWatch log group/stream.

        Args:
            config: Log query configuration

        Returns:
            Response containing log events
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._get_log_events, config
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Get log events failed: {str(e)}"]
            )

    def _get_log_events(self, config: LogQueryConfig) -> AWSServiceResponse:
        """Get log events from CloudWatch log group/stream.

        Args:
            config: Log query configuration

        Returns:
            Log events response
        """
        logs_client = self._get_boto3_client("logs")

        try:
            if config.log_stream_name:
                # Get events from specific log stream
                get_params = {
                    "logGroupName": config.log_group_name,
                    "logStreamName": config.log_stream_name,
                    "limit": config.limit,
                }

                if config.start_time:
                    get_params["startTime"] = config.start_time
                if config.end_time:
                    get_params["endTime"] = config.end_time

                response = logs_client.get_log_events(**get_params)
                events = response["events"]

            else:
                # Filter events across all streams
                filter_params = {
                    "logGroupName": config.log_group_name,
                    "limit": config.limit,
                }

                if config.start_time:
                    filter_params["startTime"] = config.start_time
                if config.end_time:
                    filter_params["endTime"] = config.end_time

                response = logs_client.filter_log_events(**filter_params)
                events = response["events"]

            formatted_events: list[dict[str, Any]] = []
            for event in events:
                formatted_events.append(
                    {
                        "timestamp": event["timestamp"],
                        "message": event["message"],
                        "ingestion_time": event.get("ingestionTime"),
                        "log_stream_name": event.get(
                            "logStreamName", config.log_stream_name
                        ),
                        "event_id": event.get("eventId"),
                    }
                )

            return AWSServiceResponse(
                status="success",
                resource={
                    "log_events": formatted_events,
                    "count": len(formatted_events),
                    "log_group_name": config.log_group_name,
                    "log_stream_name": config.log_stream_name,
                    "start_time": config.start_time,
                    "end_time": config.end_time,
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                stream_desc = config.log_stream_name or "all streams"
                return AWSServiceResponse(
                    status="not_found",
                    errors=[
                        f"Log group or stream not found: "
                        f"{config.log_group_name}/{stream_desc}"
                    ],
                )
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS CloudWatch Logs error ({error_code}): {error_message}"],
            )
