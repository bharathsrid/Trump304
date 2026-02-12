"""AWS CDK stack defining all Trump304 infrastructure."""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_iam as iam,
    aws_scheduler as scheduler,
)
from constructs import Construct


class Trump304Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ─── DynamoDB Tables ───────────────────────────────────────

        games_table = dynamodb.Table(
            self, "GamesTable",
            table_name="Trump304Games",
            partition_key=dynamodb.Attribute(
                name="game_code",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )

        connections_table = dynamodb.Table(
            self, "ConnectionsTable",
            table_name="Trump304Connections",
            partition_key=dynamodb.Attribute(
                name="connection_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # GSI on connections table for looking up by game_code
        connections_table.add_global_secondary_index(
            index_name="game-code-index",
            partition_key=dynamodb.Attribute(
                name="game_code",
                type=dynamodb.AttributeType.STRING,
            ),
        )

        # ─── Lambda Functions ──────────────────────────────────────

        lambda_code = _lambda.Code.from_asset("../lambda")

        # Common environment variables (websocket URL added later)
        common_env = {
            "GAMES_TABLE": games_table.table_name,
            "CONNECTIONS_TABLE": connections_table.table_name,
            "AWS_REGION_OVERRIDE": "ap-south-1",
        }

        # REST handler
        rest_lambda = _lambda.Function(
            self, "RestHandler",
            function_name="trump304-rest",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handlers.rest.handler",
            code=lambda_code,
            memory_size=256,
            timeout=Duration.seconds(10),
            environment=common_env,
        )
        games_table.grant_read_write_data(rest_lambda)
        connections_table.grant_read_write_data(rest_lambda)

        # WebSocket handler
        websocket_lambda = _lambda.Function(
            self, "WebSocketHandler",
            function_name="trump304-websocket",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handlers.websocket.handler",
            code=lambda_code,
            memory_size=256,
            timeout=Duration.seconds(10),
            environment=common_env,
        )
        games_table.grant_read_write_data(websocket_lambda)
        connections_table.grant_read_write_data(websocket_lambda)

        # Timer handler
        timer_lambda = _lambda.Function(
            self, "TimerHandler",
            function_name="trump304-timer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handlers.timer.handler",
            code=lambda_code,
            memory_size=256,
            timeout=Duration.seconds(10),
            environment=common_env,
        )
        games_table.grant_read_write_data(timer_lambda)
        connections_table.grant_read_write_data(timer_lambda)

        # ─── REST API ─────────────────────────────────────────────

        rest_api = apigw.RestApi(
            self, "RestApi",
            rest_api_name="Trump304 REST API",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )

        games_resource = rest_api.root.add_resource("games")
        games_resource.add_method(
            "POST",
            apigw.LambdaIntegration(rest_lambda),
        )

        game_code_resource = games_resource.add_resource("{code}")
        game_code_resource.add_method(
            "GET",
            apigw.LambdaIntegration(rest_lambda),
        )

        join_resource = game_code_resource.add_resource("join")
        join_resource.add_method(
            "POST",
            apigw.LambdaIntegration(rest_lambda),
        )

        # ─── WebSocket API ────────────────────────────────────────

        websocket_api = apigwv2.WebSocketApi(
            self, "WebSocketApi",
            api_name="Trump304 WebSocket API",
            connect_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_integrations.WebSocketLambdaIntegration(
                    "ConnectIntegration", websocket_lambda,
                ),
            ),
            disconnect_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_integrations.WebSocketLambdaIntegration(
                    "DisconnectIntegration", websocket_lambda,
                ),
            ),
            default_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_integrations.WebSocketLambdaIntegration(
                    "DefaultIntegration", websocket_lambda,
                ),
            ),
        )

        websocket_stage = apigwv2.WebSocketStage(
            self, "WebSocketStage",
            web_socket_api=websocket_api,
            stage_name="prod",
            auto_deploy=True,
        )

        # Grant WebSocket management permissions
        websocket_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["execute-api:ManageConnections"],
            resources=[
                f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/*"
            ],
        ))
        timer_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["execute-api:ManageConnections"],
            resources=[
                f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/*"
            ],
        ))

        # Update Lambda env vars with WebSocket URL
        ws_url = f"wss://{websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/prod"
        ws_endpoint = f"https://{websocket_api.api_id}.execute-api.{self.region}.amazonaws.com/prod"

        rest_lambda.add_environment("WEBSOCKET_URL", ws_url)
        websocket_lambda.add_environment("WEBSOCKET_URL", ws_url)
        timer_lambda.add_environment("WEBSOCKET_ENDPOINT", ws_endpoint)

        # ─── EventBridge Scheduler ─────────────────────────────────

        # Scheduler group for turn timers
        scheduler_group = scheduler.CfnScheduleGroup(
            self, "TimerScheduleGroup",
            name="trump304-timers",
        )

        # IAM role for EventBridge to invoke timer Lambda
        scheduler_role = iam.Role(
            self, "SchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )
        timer_lambda.grant_invoke(scheduler_role)

        # Grant websocket Lambda permission to create schedules
        websocket_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "scheduler:CreateSchedule",
                "scheduler:DeleteSchedule",
            ],
            resources=["*"],
        ))
        websocket_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=[scheduler_role.role_arn],
        ))

        websocket_lambda.add_environment("TIMER_LAMBDA_ARN", timer_lambda.function_arn)
        websocket_lambda.add_environment("TIMER_ROLE_ARN", scheduler_role.role_arn)

        # ─── Outputs ──────────────────────────────────────────────

        CfnOutput(self, "RestApiUrl",
                  value=rest_api.url,
                  description="REST API endpoint URL")

        CfnOutput(self, "WebSocketUrl",
                  value=ws_url,
                  description="WebSocket API endpoint URL")

        CfnOutput(self, "GamesTableName",
                  value=games_table.table_name)

        CfnOutput(self, "ConnectionsTableName",
                  value=connections_table.table_name)
