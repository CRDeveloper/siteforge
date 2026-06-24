"""
SharedStack — deployed once per AWS account.
Creates reusable IAM policies and SSM namespace.
"""
import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ses as ses,
)
from constructs import Construct


class SharedStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ── SSM Parameter Store namespace marker ────────────────────────────
        ssm.StringParameter(
            self,
            "SiteForgeNamespace",
            parameter_name="/siteforge/_platform/version",
            string_value="1.1.0",
            description="SiteForge platform version marker",
        )

        # ── Reusable managed policy for Lambda execution ─────────────────────
        self.lambda_base_policy = iam.ManagedPolicy(
            self,
            "LambdaBasePolicy",
            managed_policy_name="SiteForge-Lambda-Base",
            description="Base permissions for all SiteForge Lambda functions",
            statements=[
                # CloudWatch Logs
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=["arn:aws:logs:*:*:*"],
                ),
                # SSM — read site secrets
                iam.PolicyStatement(
                    actions=["ssm:GetParameter", "ssm:GetParameters"],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/siteforge/*"
                    ],
                ),
                # SES — send email (fallback/production mode)
                iam.PolicyStatement(
                    actions=["ses:SendEmail", "ses:SendTemplatedEmail", "ses:SendRawEmail"],
                    resources=["*"],
                ),
                # X-Ray tracing
                iam.PolicyStatement(
                    actions=["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                    resources=["*"],
                ),
            ],
        )

        # ── Output ───────────────────────────────────────────────────────────
        cdk.CfnOutput(
            self,
            "LambdaBasePolicyArn",
            value=self.lambda_base_policy.managed_policy_arn,
            export_name="SiteForge-LambdaBasePolicyArn",
        )
