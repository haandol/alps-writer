import * as path from "path";
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { Platform } from "aws-cdk-lib/aws-ecr-assets";
import { ApplicationLoadBalancedFargateService } from "aws-cdk-lib/aws-ecs-patterns";
import { Construct } from "constructs";

export interface IProps {
  readonly cluster: ecs.ICluster;
  readonly loadBalancer: elbv2.IApplicationLoadBalancer;
  readonly appRegion: ssm.IStringParameter;
  readonly bedrockModelId: ssm.IStringParameter;
  readonly historyTableName: ssm.IStringParameter;
  readonly chainlitAuthSecret: secretsmanager.ISecret;
  readonly tavilyApiKey: ssm.IStringParameter;
  readonly disableOauth: ssm.IStringParameter;
  readonly cognitoDomain: ssm.IStringParameter;
  readonly cognitoClientId: ssm.IStringParameter;
  readonly cognitoClientSecret: secretsmanager.ISecret;
  readonly chainlitUrl: ssm.IStringParameter;
}

export class AlpsChainlitApp extends Construct {
  readonly service: ApplicationLoadBalancedFargateService;

  constructor(scope: Construct, id: string, props: IProps) {
    super(scope, id);

    // create app service
    this.service = this.createAlbFargateService(props);
  }

  private createAlbFargateService(
    props: IProps
  ): ApplicationLoadBalancedFargateService {
    const executionRole = this.createExecutionRole();
    const taskRole = this.createEcsTaskRole(props.historyTableName.stringValue);

    const secrets: { [key: string]: ecs.Secret } = {
      AWS_REGION: ecs.Secret.fromSsmParameter(props.appRegion),
      AWS_BEDROCK_MODEL_ID: ecs.Secret.fromSsmParameter(props.bedrockModelId),
      HISTORY_TABLE_NAME: ecs.Secret.fromSsmParameter(props.historyTableName),
      CHAINLIT_AUTH_SECRET: ecs.Secret.fromSecretsManager(
        props.chainlitAuthSecret
      ),
      TAVILY_API_KEY: ecs.Secret.fromSsmParameter(props.tavilyApiKey),
      DISABLE_OAUTH: ecs.Secret.fromSsmParameter(props.disableOauth),
      OAUTH_COGNITO_DOMAIN: ecs.Secret.fromSsmParameter(props.cognitoDomain),
      OAUTH_COGNITO_CLIENT_ID: ecs.Secret.fromSsmParameter(
        props.cognitoClientId
      ),
      OAUTH_COGNITO_CLIENT_SECRET: ecs.Secret.fromSecretsManager(
        props.cognitoClientSecret
      ),
      CHAINLIT_URL: ecs.Secret.fromSsmParameter(props.chainlitUrl),
    };

    const service = new ApplicationLoadBalancedFargateService(
      this,
      "AlbFargateService",
      {
        cluster: props.cluster,
        loadBalancer: props.loadBalancer,
        taskSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        circuitBreaker: { rollback: true },
        publicLoadBalancer: false,
        openListener: false,
        platformVersion: ecs.FargatePlatformVersion.LATEST,
        cloudMapOptions: {
          name: "alps-chainlit-app",
        },
        taskImageOptions: {
          taskRole,
          executionRole,
          image: ecs.ContainerImage.fromAsset(
            path.join(__dirname, "..", "..", "..", "app"),
            {
              file: "Dockerfile",
              platform: Platform.LINUX_AMD64,
            }
          ),
          command: [
            "uv",
            "run",
            "--",
            "chainlit",
            "run",
            "app.py",
            "-h",
            "--host",
            "0.0.0.0",
          ],
          containerPort: 8000,
          secrets,
        },
        healthCheck: {
          command: ["CMD-SHELL", "curl -f http://localhost:8000/ || exit 1"],
        },
        listenerPort: 8000,
        runtimePlatform: {
          cpuArchitecture: ecs.CpuArchitecture.X86_64,
          operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
        },
        minHealthyPercent: 50,
        desiredCount: 2,
        cpu: 1024,
        memoryLimitMiB: 2048,
      }
    );

    // auto scale task count
    const scalableTarget = service.service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 5,
    });
    scalableTarget.scaleOnCpuUtilization("CpuScaling", {
      targetUtilizationPercent: 80,
    });
    scalableTarget.scaleOnMemoryUtilization("MemoryScaling", {
      targetUtilizationPercent: 80,
    });

    // enable sticky session - alb managed cookie
    service.targetGroup.enableCookieStickiness(cdk.Duration.days(1));

    // allow traffic from VPC CIDR
    service.loadBalancer.connections.allowFrom(
      ec2.Peer.ipv4(props.cluster.vpc.vpcCidrBlock),
      ec2.Port.tcp(8000),
      "Allow 8000 from app security group"
    );

    new cdk.CfnOutput(this, "ChainlitAppDns", {
      value: service.loadBalancer.loadBalancerDnsName,
    });

    return service;
  }

  private createExecutionRole(): iam.Role {
    const role = new iam.Role(this, "ExecutionRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    });
    // for cloudwatch
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: ["*"],
      })
    );
    // for xray
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
        resources: ["*"],
      })
    );
    // for ssm
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["ssm:GetParameter"],
        resources: ["*"],
      })
    );
    // for secrets
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: ["kms:Decrypt", "secretsmanager:GetSecretValue"],
        resources: ["*"],
      })
    );
    // for ecr
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
        ],
        resources: ["*"],
      })
    );
    return role;
  }

  private createEcsTaskRole(tableName: string): iam.Role {
    const role = new iam.Role(this, "TaskRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    });
    // for bedrock invoke model
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );
    // for s3
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:PutObject", "s3:GetObject"],
        resources: ["*"],
      })
    );
    // for dynamodb
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          // IndexAccess
          "dynamodb:GetShardIterator",
          "dynamodb:Scan",
          "dynamodb:Query",
          // TableAccess
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:ConditionCheckItem",
          "dynamodb:PutItem",
          "dynamodb:DescribeTable",
          "dynamodb:DeleteItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
        ],
        resources: [
          `arn:aws:dynamodb:*:${cdk.Stack.of(this).account}:table/${tableName}`,
          `arn:aws:dynamodb:*:${
            cdk.Stack.of(this).account
          }:table/${tableName}/index/*`,
        ],
      })
    );
    // for cognito sign in
    role.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["cognito-idp:InitiateAuth", "cognito-idp:GetUser"],
        resources: ["*"],
      })
    );
    return role;
  }
}
