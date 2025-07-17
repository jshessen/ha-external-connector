"""
AWS Resource Manager - Pure JSON CRUD interface over AWS resources

This module provides a modern Python implementation of the AWS resource management 
functionality originally implemented in bash aws_manager.sh.

Key Features:
- Pure JSON CRUD operations for AWS resources
- Type-safe resource specifications using pydantic
- Comprehensive error handling and validation
- Support for Lambda, IAM, SSM, CloudWatch Logs, and trigger resources
- URL management for Lambda functions
- Structured logging and monitoring
"""

from __future__ import annotations

import json
import os
import zipfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, Field

from ..utils import HAConnectorLogger, ValidationError, AWSError


class AWSResourceType(str, Enum):
    """Supported AWS resource types"""
    LAMBDA = "lambda"
    IAM = "iam"
    SSM = "ssm"
    LOGS = "logs"
    TRIGGER = "trigger"


class LambdaResourceSpec(BaseModel):
    """Specification for Lambda function resources"""
    function_name: str = Field(..., description="Name of the Lambda function")
    runtime: str = Field(default="python3.11", description="Runtime environment")
    handler: str = Field(..., description="Handler function (e.g., index.lambda_handler)")
    role_arn: str = Field(..., description="IAM role ARN for the function")
    package_path: str = Field(..., description="Path to the deployment package")
    create_url: bool = Field(default=False, description="Whether to create function URL")
    url_auth_type: str = Field(default="NONE", description="Function URL auth type")
    timeout: int = Field(default=30, description="Function timeout in seconds")
    memory_size: int = Field(default=128, description="Memory size in MB")
    description: Optional[str] = Field(None, description="Function description")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="Environment variables")


class IAMResourceSpec(BaseModel):
    """Specification for IAM resources"""
    resource_type: str = Field(..., description="Type of IAM resource (role, policy)")
    name: str = Field(..., description="Name of the IAM resource")
    assume_role_policy: Optional[Dict[str, Any]] = Field(None, description="Trust policy for roles")
    policy_document: Optional[Dict[str, Any]] = Field(None, description="Policy document")
    description: Optional[str] = Field(None, description="Resource description")


class SSMResourceSpec(BaseModel):
    """Specification for SSM Parameter resources"""
    name: str = Field(..., description="Parameter name")
    value: str = Field(..., description="Parameter value")
    parameter_type: str = Field(default="String", description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    secure: bool = Field(default=False, description="Whether to use SecureString type")


class LogsResourceSpec(BaseModel):
    """Specification for CloudWatch Logs resources"""
    log_group_name: str = Field(..., description="Log group name")
    retention_days: int = Field(default=14, description="Log retention in days")


class AWSResourceResponse(BaseModel):
    """Standard response format for AWS operations"""
    status: str = Field(..., description="Operation status (created, updated, error, etc.)")
    resource: Optional[Dict[str, Any]] = Field(None, description="Resource data")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    exists: Optional[bool] = Field(None, description="Whether resource exists (for read operations)")


class AWSBaseManager:
    """Base class for AWS resource managers"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.logger = HAConnectorLogger("aws_manager")
        
    def _handle_boto_error(self, error: Exception, operation: str) -> AWSResourceResponse:
        """Handle boto3 errors and return standardized error response"""
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', 'Unknown')
            error_message = error.response.get('Error', {}).get('Message', str(error))
            self.logger.error(f"AWS {operation} failed: {error_code} - {error_message}")
            return AWSResourceResponse(
                status="error",
                errors=[f"AWS {operation} failed: {error_code} - {error_message}"]
            )
        else:
            self.logger.error(f"AWS {operation} failed: {str(error)}")
            return AWSResourceResponse(
                status="error",
                errors=[f"AWS {operation} failed: {str(error)}"]
            )


class AWSLambdaManager(AWSBaseManager):
    """Manager for AWS Lambda functions"""
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(region)
        self.client = boto3.client('lambda', region_name=region)
        
    def create_or_update(self, spec: LambdaResourceSpec) -> AWSResourceResponse:
        """Create or update a Lambda function"""
        try:
            # Check if function exists
            function_exists = self._function_exists(spec.function_name)
            
            if function_exists:
                return self._update_function(spec)
            else:
                return self._create_function(spec)
                
        except Exception as e:
            return self._handle_boto_error(e, "Lambda create/update")
    
    def read(self, function_name: str) -> AWSResourceResponse:
        """Read Lambda function configuration"""
        try:
            response = self.client.get_function(FunctionName=function_name)
            
            # Try to get function URL if it exists
            url_config = None
            try:
                url_response = self.client.get_function_url_config(FunctionName=function_name)
                url_config = url_response
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            # Add URL config to response
            if url_config:
                response['Configuration']['FunctionUrl'] = url_config
            else:
                response['Configuration']['FunctionUrl'] = None
                
            return AWSResourceResponse(
                status="success",
                resource=response,
                exists=True
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return AWSResourceResponse(
                    status="success",
                    exists=False,
                    errors=[]
                )
            return self._handle_boto_error(e, "Lambda read")
        except Exception as e:
            return self._handle_boto_error(e, "Lambda read")
    
    def delete(self, function_name: str) -> AWSResourceResponse:
        """Delete Lambda function (placeholder - not implemented in original)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["Lambda delete not implemented"]
        )
    
    def _function_exists(self, function_name: str) -> bool:
        """Check if Lambda function exists"""
        try:
            self.client.get_function(FunctionName=function_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise
    
    def _create_function(self, spec: LambdaResourceSpec) -> AWSResourceResponse:
        """Create new Lambda function"""
        # Read the package file
        with open(spec.package_path, 'rb') as package_file:
            package_bytes = package_file.read()
        
        create_params = {
            'FunctionName': spec.function_name,
            'Runtime': spec.runtime,
            'Role': spec.role_arn,
            'Handler': spec.handler,
            'Code': {'ZipFile': package_bytes},
            'Timeout': spec.timeout,
            'MemorySize': spec.memory_size,
        }
        
        if spec.description:
            create_params['Description'] = spec.description
            
        if spec.environment_variables:
            create_params['Environment'] = {'Variables': spec.environment_variables}
        
        # Create the function
        self.client.create_function(**create_params)
        
        # Get the created function details
        function_data = self.client.get_function(FunctionName=spec.function_name)
        
        # Create function URL if requested
        if spec.create_url:
            try:
                url_response = self.client.create_function_url_config(
                    FunctionName=spec.function_name,
                    AuthType=spec.url_auth_type
                )
                function_data['Configuration']['FunctionUrl'] = url_response
            except Exception as e:
                self.logger.warning(f"Failed to create function URL: {str(e)}")
                function_data['Configuration']['FunctionUrl'] = None
        else:
            function_data['Configuration']['FunctionUrl'] = None
        
        self.logger.info(f"Created Lambda function: {spec.function_name}")
        return AWSResourceResponse(
            status="created",
            resource=function_data
        )
    
    def _update_function(self, spec: LambdaResourceSpec) -> AWSResourceResponse:
        """Update existing Lambda function"""
        # Update function code
        with open(spec.package_path, 'rb') as package_file:
            package_bytes = package_file.read()
        
        self.client.update_function_code(
            FunctionName=spec.function_name,
            ZipFile=package_bytes
        )
        
        # Update function configuration
        update_params = {
            'FunctionName': spec.function_name,
            'Runtime': spec.runtime,
            'Role': spec.role_arn,
            'Handler': spec.handler,
            'Timeout': spec.timeout,
            'MemorySize': spec.memory_size,
        }
        
        if spec.description:
            update_params['Description'] = spec.description
            
        if spec.environment_variables:
            update_params['Environment'] = {'Variables': spec.environment_variables}
        
        self.client.update_function_configuration(**update_params)
        
        # Get updated function details
        function_data = self.client.get_function(FunctionName=spec.function_name)
        
        # Handle function URL
        if spec.create_url:
            try:
                # Try to get existing URL
                url_response = self.client.get_function_url_config(FunctionName=spec.function_name)
                function_data['Configuration']['FunctionUrl'] = url_response
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Create URL if it doesn't exist
                    try:
                        url_response = self.client.create_function_url_config(
                            FunctionName=spec.function_name,
                            AuthType=spec.url_auth_type
                        )
                        function_data['Configuration']['FunctionUrl'] = url_response
                    except Exception as create_error:
                        self.logger.warning(f"Failed to create function URL: {str(create_error)}")
                        function_data['Configuration']['FunctionUrl'] = None
                else:
                    raise
        else:
            function_data['Configuration']['FunctionUrl'] = None
        
        self.logger.info(f"Updated Lambda function: {spec.function_name}")
        return AWSResourceResponse(
            status="updated",
            resource=function_data
        )


class AWSIAMManager(AWSBaseManager):
    """Manager for AWS IAM resources"""
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(region)
        self.client = boto3.client('iam', region_name=region)
    
    def create_or_update(self, spec: IAMResourceSpec) -> AWSResourceResponse:
        """Create or update IAM resource"""
        try:
            if spec.resource_type == "role":
                return self._create_or_update_role(spec)
            elif spec.resource_type == "policy":
                return self._create_or_update_policy(spec)
            else:
                return AWSResourceResponse(
                    status="error",
                    errors=[f"Unknown IAM resource type: {spec.resource_type}"]
                )
        except Exception as e:
            return self._handle_boto_error(e, "IAM create/update")
    
    def read(self, resource_name: str, resource_type: str = "role") -> AWSResourceResponse:
        """Read IAM resource"""
        try:
            if resource_type == "role":
                response = self.client.get_role(RoleName=resource_name)
                return AWSResourceResponse(
                    status="success",
                    resource=response,
                    exists=True
                )
            elif resource_type == "policy":
                # This is more complex as we need the policy ARN
                return AWSResourceResponse(
                    status="error",
                    errors=["Policy reading requires ARN, not implemented"]
                )
            else:
                return AWSResourceResponse(
                    status="error",
                    errors=[f"Unknown IAM resource type: {resource_type}"]
                )
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return AWSResourceResponse(
                    status="success",
                    exists=False
                )
            return self._handle_boto_error(e, "IAM read")
        except Exception as e:
            return self._handle_boto_error(e, "IAM read")
    
    def delete(self, resource_name: str, resource_type: str = "role") -> AWSResourceResponse:
        """Delete IAM resource (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=[f"IAM {resource_type} delete not implemented"]
        )
    
    def _create_or_update_role(self, spec: IAMResourceSpec) -> AWSResourceResponse:
        """Create or update IAM role"""
        try:
            # Check if role exists
            try:
                self.client.get_role(RoleName=spec.name)
                role_exists = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    role_exists = False
                else:
                    raise
            
            if role_exists:
                # Update role's assume role policy if provided
                if spec.assume_role_policy:
                    self.client.update_assume_role_policy(
                        RoleName=spec.name,
                        PolicyDocument=json.dumps(spec.assume_role_policy)
                    )
                
                response = self.client.get_role(RoleName=spec.name)
                self.logger.info(f"Updated IAM role: {spec.name}")
                return AWSResourceResponse(
                    status="updated",
                    resource=response
                )
            else:
                # Create new role
                create_params = {
                    'RoleName': spec.name,
                    'AssumeRolePolicyDocument': json.dumps(spec.assume_role_policy),
                }
                
                if spec.description:
                    create_params['Description'] = spec.description
                
                response = self.client.create_role(**create_params)
                self.logger.info(f"Created IAM role: {spec.name}")
                return AWSResourceResponse(
                    status="created",
                    resource=response
                )
                
        except Exception as e:
            return self._handle_boto_error(e, "IAM role create/update")
    
    def _create_or_update_policy(self, spec: IAMResourceSpec) -> AWSResourceResponse:
        """Create or update IAM policy (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["IAM policy create/update not implemented"]
        )


class AWSSSMManager(AWSBaseManager):
    """Manager for AWS Systems Manager parameters"""
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(region)
        self.client = boto3.client('ssm', region_name=region)
    
    def create_or_update(self, spec: SSMResourceSpec) -> AWSResourceResponse:
        """Create or update SSM parameter"""
        try:
            parameter_type = "SecureString" if spec.secure else spec.parameter_type
            
            put_params = {
                'Name': spec.name,
                'Value': spec.value,
                'Type': parameter_type,
                'Overwrite': True,  # Allow updates
            }
            
            if spec.description:
                put_params['Description'] = spec.description
            
            self.client.put_parameter(**put_params)
            
            # Get the parameter to return in response
            response = self.client.get_parameter(Name=spec.name, WithDecryption=True)
            
            self.logger.info(f"Created/updated SSM parameter: {spec.name}")
            return AWSResourceResponse(
                status="created",
                resource=response
            )
            
        except Exception as e:
            return self._handle_boto_error(e, "SSM create/update")
    
    def read(self, parameter_name: str) -> AWSResourceResponse:
        """Read SSM parameter"""
        try:
            response = self.client.get_parameter(Name=parameter_name, WithDecryption=True)
            return AWSResourceResponse(
                status="success",
                resource=response,
                exists=True
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                return AWSResourceResponse(
                    status="success",
                    exists=False
                )
            return self._handle_boto_error(e, "SSM read")
        except Exception as e:
            return self._handle_boto_error(e, "SSM read")
    
    def delete(self, parameter_name: str) -> AWSResourceResponse:
        """Delete SSM parameter (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["SSM parameter delete not implemented"]
        )


class AWSLogsManager(AWSBaseManager):
    """Manager for AWS CloudWatch Logs"""
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(region)
        self.client = boto3.client('logs', region_name=region)
    
    def create_or_update(self, spec: LogsResourceSpec) -> AWSResourceResponse:
        """Create or update CloudWatch log group"""
        try:
            # Check if log group exists
            try:
                self.client.describe_log_groups(logGroupNamePrefix=spec.log_group_name)
                log_group_exists = True
            except ClientError:
                log_group_exists = False
            
            if not log_group_exists:
                # Create log group
                self.client.create_log_group(logGroupName=spec.log_group_name)
                
                # Set retention policy
                self.client.put_retention_policy(
                    logGroupName=spec.log_group_name,
                    retentionInDays=spec.retention_days
                )
                
                self.logger.info(f"Created CloudWatch log group: {spec.log_group_name}")
                status = "created"
            else:
                # Update retention policy
                self.client.put_retention_policy(
                    logGroupName=spec.log_group_name,
                    retentionInDays=spec.retention_days
                )
                
                self.logger.info(f"Updated CloudWatch log group: {spec.log_group_name}")
                status = "updated"
            
            # Get log group details
            response = self.client.describe_log_groups(logGroupNamePrefix=spec.log_group_name)
            
            return AWSResourceResponse(
                status=status,
                resource=response
            )
            
        except Exception as e:
            return self._handle_boto_error(e, "CloudWatch Logs create/update")
    
    def read(self, log_group_name: str) -> AWSResourceResponse:
        """Read CloudWatch log group"""
        try:
            response = self.client.describe_log_groups(logGroupNamePrefix=log_group_name)
            
            if response.get('logGroups'):
                return AWSResourceResponse(
                    status="success",
                    resource=response,
                    exists=True
                )
            else:
                return AWSResourceResponse(
                    status="success",
                    exists=False
                )
                
        except Exception as e:
            return self._handle_boto_error(e, "CloudWatch Logs read")
    
    def delete(self, log_group_name: str) -> AWSResourceResponse:
        """Delete CloudWatch log group (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["CloudWatch Logs delete not implemented"]
        )


class AWSTriggerManager(AWSBaseManager):
    """Manager for AWS triggers (placeholder)"""
    
    def create_or_update(self, spec: Dict[str, Any]) -> AWSResourceResponse:
        """Create or update trigger (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["Trigger resource creation not implemented"]
        )
    
    def read(self, trigger_id: str) -> AWSResourceResponse:
        """Read trigger (placeholder)"""
        return AWSResourceResponse(
            status="success",
            exists=False,
            errors=["Trigger resource reading not implemented"]
        )
    
    def delete(self, trigger_id: str) -> AWSResourceResponse:
        """Delete trigger (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["Trigger delete not implemented"]
        )


class AWSResourceManager:
    """Main AWS resource manager providing CRUD operations for all resource types"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.logger = HAConnectorLogger("aws_resource_manager")
        
        # Initialize resource managers
        self.lambda_manager = AWSLambdaManager(region)
        self.iam_manager = AWSIAMManager(region)
        self.ssm_manager = AWSSSMManager(region)
        self.logs_manager = AWSLogsManager(region)
        self.trigger_manager = AWSTriggerManager(region)
    
    def create_resource(self, resource_type: AWSResourceType, resource_spec: Dict[str, Any]) -> AWSResourceResponse:
        """Create a resource based on type and specification"""
        try:
            if resource_type == AWSResourceType.LAMBDA:
                spec = LambdaResourceSpec(**resource_spec)
                return self.lambda_manager.create_or_update(spec)
            elif resource_type == AWSResourceType.IAM:
                spec = IAMResourceSpec(**resource_spec)
                return self.iam_manager.create_or_update(spec)
            elif resource_type == AWSResourceType.SSM:
                spec = SSMResourceSpec(**resource_spec)
                return self.ssm_manager.create_or_update(spec)
            elif resource_type == AWSResourceType.LOGS:
                spec = LogsResourceSpec(**resource_spec)
                return self.logs_manager.create_or_update(spec)
            elif resource_type == AWSResourceType.TRIGGER:
                return self.trigger_manager.create_or_update(resource_spec)
            else:
                return AWSResourceResponse(
                    status="error",
                    errors=[f"Unknown resource type: {resource_type}"]
                )
        except ValidationError as e:
            return AWSResourceResponse(
                status="error",
                errors=[f"Invalid resource specification: {str(e)}"]
            )
        except Exception as e:
            self.logger.error(f"Resource creation failed for {resource_type}: {str(e)}")
            return AWSResourceResponse(
                status="error",
                errors=[f"Resource creation failed: {str(e)}"]
            )
    
    def read_resource(self, resource_type: AWSResourceType, resource_id: str, **kwargs) -> AWSResourceResponse:
        """Read a resource's current state"""
        try:
            if resource_type == AWSResourceType.LAMBDA:
                return self.lambda_manager.read(resource_id)
            elif resource_type == AWSResourceType.IAM:
                resource_subtype = kwargs.get('resource_subtype', 'role')
                return self.iam_manager.read(resource_id, resource_subtype)
            elif resource_type == AWSResourceType.SSM:
                return self.ssm_manager.read(resource_id)
            elif resource_type == AWSResourceType.LOGS:
                return self.logs_manager.read(resource_id)
            elif resource_type == AWSResourceType.TRIGGER:
                return self.trigger_manager.read(resource_id)
            else:
                return AWSResourceResponse(
                    status="success",
                    exists=False,
                    errors=[f"Unknown resource type: {resource_type}"]
                )
        except Exception as e:
            self.logger.error(f"Resource read failed for {resource_type} {resource_id}: {str(e)}")
            return AWSResourceResponse(
                status="error",
                errors=[f"Resource read failed: {str(e)}"]
            )
    
    def update_resource(self, resource_type: AWSResourceType, resource_id: str, resource_spec: Dict[str, Any]) -> AWSResourceResponse:
        """Update a resource"""
        # For most resources, update is the same as create_or_update
        return self.create_resource(resource_type, resource_spec)
    
    def delete_resource(self, resource_type: AWSResourceType, resource_id: str) -> AWSResourceResponse:
        """Delete a resource"""
        try:
            if resource_type == AWSResourceType.LAMBDA:
                return self.lambda_manager.delete(resource_id)
            elif resource_type == AWSResourceType.IAM:
                return self.iam_manager.delete(resource_id)
            elif resource_type == AWSResourceType.SSM:
                return self.ssm_manager.delete(resource_id)
            elif resource_type == AWSResourceType.LOGS:
                return self.logs_manager.delete(resource_id)
            elif resource_type == AWSResourceType.TRIGGER:
                return self.trigger_manager.delete(resource_id)
            else:
                return AWSResourceResponse(
                    status="error",
                    errors=[f"Unknown resource type: {resource_type}"]
                )
        except Exception as e:
            self.logger.error(f"Resource deletion failed for {resource_type} {resource_id}: {str(e)}")
            return AWSResourceResponse(
                status="error",
                errors=[f"Resource deletion failed: {str(e)}"]
            )
    
    def validate_aws_access(self) -> AWSResourceResponse:
        """Validate AWS access and permissions"""
        try:
            # Try to get caller identity
            sts_client = boto3.client('sts', region_name=self.region)
            identity = sts_client.get_caller_identity()
            
            self.logger.info(f"AWS access validated for account: {identity.get('Account')}, user: {identity.get('UserId')}")
            
            return AWSResourceResponse(
                status="success",
                resource=identity,
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"AWS access validation failed: {str(e)}")
            return AWSResourceResponse(
                status="error",
                errors=[f"AWS access validation failed: {str(e)}"]
            )


def validate_aws_access(region: str = "us-east-1") -> Dict[str, Any]:
    """Validate AWS access and return JSON response"""
    manager = AWSResourceManager(region)
    response = manager.validate_aws_access()
    return response.dict()


# Global instance for backwards compatibility
_global_manager: Optional[AWSResourceManager] = None


def get_aws_manager(region: str = "us-east-1") -> AWSResourceManager:
    """Get or create global AWS resource manager instance"""
    global _global_manager
    if _global_manager is None or _global_manager.region != region:
        _global_manager = AWSResourceManager(region)
    return _global_manager
