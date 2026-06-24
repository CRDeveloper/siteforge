"""
SiteStack — all infrastructure for one client website.
Deploys: S3, CloudFront, ACM, DynamoDB, Lambda, API Gateway, EventBridge.
"""
import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cf,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_apigatewayv2_authorizers as authorizers,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3_deployment as s3deploy,
    Duration, RemovalPolicy,
)
from constructs import Construct
from pathlib import Path
import json


class SiteStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        site_config: dict,
        shared_stack,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        site_id = site_config["siteId"]
        domain = site_config["domain"]
        admin_email = site_config["email"]["adminEmail"]

        # ── Tags applied to all resources in this stack ──────────────────────
        cdk.Tags.of(self).add("SiteForge-SiteId", site_id)
        cdk.Tags.of(self).add("SiteForge-Domain", domain)

        # ── 1. DynamoDB Table ─────────────────────────────────────────────────
        self.table = dynamodb.Table(
            self,
            "MainTable",
            table_name=f"{site_id}_main",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,  # Never auto-delete client data
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # GSI1 — query appointments by status + date (admin dashboard)
        self.table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(
                name="GSI1PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="GSI1SK", type=dynamodb.AttributeType.STRING
            ),
        )

        # GSI2 — email lookup for login
        self.table.add_global_secondary_index(
            index_name="GSI2",
            partition_key=dynamodb.Attribute(
                name="email", type=dynamodb.AttributeType.STRING
            ),
        )

        # ── 2. S3 — Frontend Bucket ───────────────────────────────────────────
        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            bucket_name=f"siteforge-{site_id}-frontend",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=False,
        )

        # ── 3. S3 — Uploads Bucket ────────────────────────────────────────────
        self.uploads_bucket = s3.Bucket(
            self,
            "UploadsBucket",
            bucket_name=f"siteforge-{site_id}-uploads",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.PUT, s3.HttpMethods.GET],
                    allowed_origins=[f"https://{domain}", f"https://www.{domain}"],
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="delete-unconfirmed-uploads",
                    prefix="tmp/",
                    expiration=Duration.days(1),
                )
            ],
        )

        # ── 4. SSL Certificate (ACM — must be us-east-1 for CloudFront) ───────
        # NOTE: Domain must be in Cloudflare. After deploy, add the CNAME
        # validation record shown in ACM console to Cloudflare DNS (DNS only mode).
        self.certificate = acm.Certificate(
            self,
            "SiteCertificate",
            domain_name=domain,
            subject_alternative_names=[f"www.{domain}"],
            validation=acm.CertificateValidation.from_dns(),
        )

        # ── 5. Lambda Function ────────────────────────────────────────────────
        # Store site config as environment variable (non-sensitive parts)
        env_config = {
            "SITE_ID": site_id,
            "TABLE_NAME": f"{site_id}_main",
            "UPLOADS_BUCKET": f"siteforge-{site_id}-uploads",
            "DOMAIN": domain,
            "DEFAULT_LANG": site_config.get("defaultLang", "en"),
            "EMAIL_PROVIDER": site_config["email"]["provider"],
            "SENDER_EMAIL": site_config["email"]["senderEmail"],
            "SENDER_NAME": site_config["email"]["senderName"],
            "ADMIN_EMAIL": admin_email,
            "BREVO_API_KEY_PARAM": site_config["email"].get(
                "apiKeyParam", f"/siteforge/{site_id}/brevo_api_key"
            ),
            "JWT_SECRET_PARAM": f"/siteforge/{site_id}/jwt_secret",
            "CANCELLATION_HOURS": str(
                site_config["appointments"]["cancellationHours"]
            ),
            "REMINDER_HOURS": str(
                site_config["appointments"]["reminderHoursBefore"]
            ),
        }

        api_code_path = str(Path(__file__).parent.parent.parent.parent / "apps" / "api")

        self.lambda_fn = lambda_.Function(
            self,
            "ApiHandler",
            function_name=f"siteforge-{site_id}-api",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="main.handler",
            code=lambda_.Code.from_asset(
                api_code_path,
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -r . /asset-output"
                    ],
                ),
            ),
            environment=env_config,
            timeout=Duration.seconds(29),
            memory_size=256,
            tracing=lambda_.Tracing.ACTIVE,
        )

        # Attach base policy + site-specific permissions
        self.lambda_fn.role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_name(
                self, "LambdaBasePolicy", "SiteForge-Lambda-Base"
            )
        )
        self.table.grant_read_write_data(self.lambda_fn)
        self.uploads_bucket.grant_read_write(self.lambda_fn)

        # ── 6. API Gateway (HTTP API v2) ──────────────────────────────────────
        self.http_api = apigw.HttpApi(
            self,
            "HttpApi",
            api_name=f"siteforge-{site_id}",
            description=f"SiteForge API — {site_config['siteName']}",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_headers=["Authorization", "Content-Type"],
                allow_methods=[
                    apigw.CorsHttpMethod.GET,
                    apigw.CorsHttpMethod.POST,
                    apigw.CorsHttpMethod.PATCH,
                    apigw.CorsHttpMethod.DELETE,
                    apigw.CorsHttpMethod.OPTIONS,
                ],
                allow_origins=[f"https://{domain}", f"https://www.{domain}"],
                max_age=Duration.hours(1),
            ),
        )

        lambda_integration = integrations.HttpLambdaIntegration(
            "LambdaIntegration", self.lambda_fn
        )

        # JWT Authorizer (validated by Lambda itself via middleware)
        jwt_authorizer = authorizers.HttpLambdaAuthorizer(
            "JwtAuthorizer",
            self.lambda_fn,
            authorizer_name=f"{site_id}-jwt-authorizer",
            identity_source=["$request.header.Authorization"],
            response_types=[authorizers.HttpLambdaResponseType.SIMPLE],
        )

        # Public routes (no auth)
        for method, path in [
            (apigw.HttpMethod.GET, "/config"),
            (apigw.HttpMethod.GET, "/services"),
            (apigw.HttpMethod.GET, "/availability"),
            (apigw.HttpMethod.POST, "/auth/register"),
            (apigw.HttpMethod.POST, "/auth/login"),
            (apigw.HttpMethod.POST, "/auth/logout"),
            (apigw.HttpMethod.GET, "/auth/verify"),
            (apigw.HttpMethod.POST, "/auth/forgot-password"),
            (apigw.HttpMethod.POST, "/auth/reset-password"),
        ]:
            self.http_api.add_routes(
                path=path,
                methods=[method],
                integration=lambda_integration,
            )

        # Protected routes (JWT required)
        for method, path in [
            (apigw.HttpMethod.GET, "/me"),
            (apigw.HttpMethod.PATCH, "/me"),
            (apigw.HttpMethod.GET, "/appointments"),
            (apigw.HttpMethod.POST, "/appointments"),
            (apigw.HttpMethod.DELETE, "/appointments/{id}"),
            (apigw.HttpMethod.GET, "/admin/appointments"),
            (apigw.HttpMethod.PATCH, "/admin/appointments/{id}"),
            (apigw.HttpMethod.POST, "/admin/appointments/{id}/message"),
            (apigw.HttpMethod.GET, "/admin/users"),
            (apigw.HttpMethod.GET, "/admin/stats"),
            (apigw.HttpMethod.GET, "/admin/services"),
            (apigw.HttpMethod.POST, "/admin/services"),
            (apigw.HttpMethod.PATCH, "/admin/services/{id}"),
            (apigw.HttpMethod.DELETE, "/admin/services/{id}"),
            (apigw.HttpMethod.GET, "/admin/availability"),
            (apigw.HttpMethod.POST, "/admin/availability"),
            (apigw.HttpMethod.DELETE, "/admin/availability/{id}"),
            (apigw.HttpMethod.GET, "/admin/config"),
            (apigw.HttpMethod.PATCH, "/admin/config"),
            (apigw.HttpMethod.POST, "/uploads/presign"),
        ]:
            self.http_api.add_routes(
                path=path,
                methods=[method],
                integration=lambda_integration,
                authorizer=jwt_authorizer,
            )

        # ── 7. CloudFront Distribution ────────────────────────────────────────
        api_origin = origins.HttpOrigin(
            f"{self.http_api.api_id}.execute-api.{self.region}.amazonaws.com",
            origin_path="/",
        )

        s3_origin = origins.S3Origin(self.frontend_bucket)

        self.distribution = cf.Distribution(
            self,
            "Distribution",
            default_behavior=cf.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            additional_behaviors={
                "/api/*": cf.BehaviorOptions(
                    origin=api_origin,
                    viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cf.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cf.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    allowed_methods=cf.AllowedMethods.ALLOW_ALL,
                )
            },
            domain_names=[domain, f"www.{domain}"],
            certificate=self.certificate,
            default_root_object="index.html",
            error_responses=[
                # SPA fallback — all 404s serve index.html (Next.js handles routing)
                cf.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cf.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
            price_class=cf.PriceClass.PRICE_CLASS_100,  # US/EU only — cheaper
        )

        # ── 8. EventBridge — Appointment Reminder Scheduler ──────────────────
        reminder_rule = events.Rule(
            self,
            "ReminderRule",
            rule_name=f"siteforge-{site_id}-reminders",
            description="Triggers Lambda to send 24h appointment reminders",
            schedule=events.Schedule.cron(hour="14", minute="0"),  # 2pm UTC daily
        )
        reminder_rule.add_target(
            targets.LambdaFunction(
                self.lambda_fn,
                event=events.RuleTargetInput.from_object(
                    {"source": "eventbridge", "action": "send_reminders"}
                ),
            )
        )

        # ── 9. SSM — Store site config JSON for Lambda runtime ────────────────
        ssm.StringParameter(
            self,
            "SiteConfigParam",
            parameter_name=f"/siteforge/{site_id}/config",
            string_value=json.dumps(site_config),
            description=f"Site config for {site_config['siteName']}",
        )

        # ── 10. Outputs ───────────────────────────────────────────────────────
        cdk.CfnOutput(self, "SiteUrl", value=f"https://{domain}")
        cdk.CfnOutput(self, "AdminUrl", value=f"https://{domain}/admin")
        cdk.CfnOutput(
            self, "CloudFrontDomain", value=self.distribution.distribution_domain_name,
            description="Add this as CNAME in Cloudflare (DNS only, no proxy)"
        )
        cdk.CfnOutput(
            self, "ApiEndpoint", value=self.http_api.api_endpoint
        )
        cdk.CfnOutput(
            self, "DynamoTableName", value=self.table.table_name
        )
        cdk.CfnOutput(
            self, "FrontendBucketName", value=self.frontend_bucket.bucket_name
        )
        cdk.CfnOutput(
            self, "UploadsBucketName", value=self.uploads_bucket.bucket_name
        )
        cdk.CfnOutput(
            self, "CertificateArn", value=self.certificate.certificate_arn,
            description="Add DNS validation CNAME from ACM console to Cloudflare"
        )
