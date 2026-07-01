"""
MonitoringStack — CloudWatch dashboards and alarms per site.
"""
import aws_cdk as cdk
from aws_cdk import (
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    Duration,
)
from constructs import Construct


class MonitoringStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        site_id: str,
        site_name: str,
        lambda_fn,
        http_api,
        table,
        admin_email: str,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # SNS topic for alarms
        alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            display_name=f"SiteForge {site_name} Alerts",
        )
        alarm_topic.add_subscription(
            subscriptions.EmailSubscription(admin_email)
        )

        # CloudWatch dashboard
        dashboard = cw.Dashboard(
            self,
            "Dashboard",
            dashboard_name=f"siteforge-{site_id}",
        )

        # Lambda metrics
        dashboard.add_widgets(
            cw.GraphWidget(
                title="Lambda Invocations & Errors",
                left=[
                    lambda_fn.metric_invocations(),
                    lambda_fn.metric_errors(),
                ],
                width=12,
            ),
            cw.GraphWidget(
                title="Lambda Duration (ms)",
                left=[lambda_fn.metric_duration()],
                width=12,
            ),
        )

        # DynamoDB metrics
        dashboard.add_widgets(
            cw.GraphWidget(
                title="DynamoDB Consumed RCU/WCU",
                left=[
                    table.metric_consumed_read_capacity_units(),
                    table.metric_consumed_write_capacity_units(),
                ],
                width=12,
            ),
            cw.GraphWidget(
                title="DynamoDB User Errors",
                left=[table.metric_user_errors()],
                width=12,
            ),
        )

        # Alarms
        lambda_fn.metric_errors().create_alarm(
            self,
            "HighErrorRate",
            threshold=5,
            evaluation_periods=1,
            alarm_description=f"Lambda errors > 5/min",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

        table.metric_user_errors().create_alarm(
            self,
            "DynamoDBErrors",
            threshold=1,
            evaluation_periods=1,
            alarm_description="DynamoDB user errors detected",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

        lambda_fn.metric_throttles().create_alarm(
            self,
            "LambdaThrottles",
            threshold=1,
            evaluation_periods=1,
            alarm_description="Lambda throttled",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # Outputs
        cdk.CfnOutput(
            self,
            "DashboardUrl",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}",
            description="CloudWatch dashboard",
        )
