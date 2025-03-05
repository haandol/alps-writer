import * as cdk from "aws-cdk-lib";
import * as apigw from "aws-cdk-lib/aws-apigatewayv2";
import * as nag from "cdk-nag";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";
import { HttpAlbIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import { AlpsChainlitApp } from "../constructs/alps-chainlit-app";

interface IProps extends cdk.StackProps {
  readonly vpc: ec2.IVpc;
  readonly userPool: cognito.IUserPool;
  readonly cognitoDomain: ssm.IStringParameter;
  readonly httpApi: apigw.IHttpApi;
  readonly vpcLink: apigw.IVpcLink;
  readonly cluster: ecs.ICluster;
  readonly loadBalancer: elbv2.IApplicationLoadBalancer;
  readonly userPoolClient: cognito.IUserPoolClient;
  readonly appRegion: string;
  readonly historyTableName: string;
  readonly tavilyApiKey: string;
  readonly callbackUrls: string[];
}

interface AppEnvVars {
  appRegion: ssm.IStringParameter;
  historyTableName: ssm.IStringParameter;
  chainlitAuthSecret: secretsmanager.ISecret;
  tavilyApiKey: ssm.IStringParameter;
  disableOauth: ssm.IStringParameter;
  chainlitUrl: ssm.IStringParameter;
  cognitoClientId: ssm.IStringParameter;
  cognitoClientSecret: secretsmanager.ISecret;
}

export class AlpsAppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: IProps) {
    super(scope, id, props);

    // setup apps
    const envVars = this.createAppEnvVars(props);
    const alpsChainlitApp = new AlpsChainlitApp(this, "AlpsChainlitApp", {
      ...props,
      ...envVars,
    });
    this.registerChainlitAppRoute(
      props.httpApi,
      props.vpcLink,
      alpsChainlitApp.service.listener
    );

    // Nag
    nag.NagSuppressions.addResourceSuppressions(envVars.chainlitAuthSecret, [
      {
        id: "AwsPrototyping-SecretsManagerRotationEnabled",
        reason:
          "Secrets Manager rotation is not enabled for this secret, which is fine for prototyping.",
      },
    ]);
    nag.NagSuppressions.addResourceSuppressions(envVars.cognitoClientSecret, [
      {
        id: "AwsPrototyping-SecretsManagerRotationEnabled",
        reason:
          "Secrets Manager rotation is not enabled for this secret, which is fine for prototyping.",
      },
    ]);
    // Unable to find a resource of this.
    nag.NagSuppressions.addStackSuppressions(this, [
      {
        id: "AwsPrototyping-IAMNoManagedPolicies",
        reason: "I do not use Lambda in this stack",
      },
      {
        id: "AwsPrototyping-APIGWAuthorization",
        reason: "Cognito is used for authorization",
      },
    ]);
  }

  private registerChainlitAppRoute(
    httpApi: apigw.IHttpApi,
    vpcLink: apigw.IVpcLink,
    listener: elbv2.IApplicationListener
  ) {
    const authIntegration = new HttpAlbIntegration(
      "ChainlitAppInteg",
      listener,
      {
        vpcLink,
      }
    );
    new apigw.HttpRoute(this, "ChainlitCognitoAuthRoute", {
      httpApi,
      routeKey: apigw.HttpRouteKey.with("/{proxy+}", apigw.HttpMethod.ANY),
      integration: authIntegration,
    });
  }

  private createAppEnvVars(props: IProps): AppEnvVars {
    const ns = this.node.tryGetContext("ns") as string;

    const appRegion = new ssm.StringParameter(this, "AppRegion", {
      description: "App region",
      parameterName: `${ns}AppRegion`,
      stringValue: props.appRegion,
      tier: ssm.ParameterTier.STANDARD,
    });
    const historyTableName = new ssm.StringParameter(this, "HistoryTableName", {
      description: "History table name",
      parameterName: `${ns}HistoryTableName`,
      stringValue: props.historyTableName,
      tier: ssm.ParameterTier.STANDARD,
    });
    const cognitoClientId = new ssm.StringParameter(this, "CognitoClientid", {
      description: "Cognito client id",
      parameterName: `${ns}CognitoClientId`,
      stringValue: props.userPoolClient.userPoolClientId,
      tier: ssm.ParameterTier.STANDARD,
    });
    const cognitoClientSecret = new secretsmanager.Secret(
      this,
      "CognitoClientSecret",
      {
        secretName: `${ns.toLowerCase()}CognitoClientSecret`,
        description: "to store env variable of ECS as secrets",
        secretStringValue: props.userPoolClient.userPoolClientSecret,
      }
    );
    const chainlitAuthSecret = new secretsmanager.Secret(
      this,
      "ChainlitAuthSecret",
      {
        secretName: `${ns}ChainlitAuthSecret`,
        description: "Auth secret for Chainlit",
        generateSecretString: {
          passwordLength: 64,
        },
      }
    );
    const tavilyApiKey = new ssm.StringParameter(this, "TavilyApiKey", {
      description: "API key for Tavily",
      parameterName: `${ns}TavilyApiKey`,
      stringValue: props.tavilyApiKey,
      tier: ssm.ParameterTier.STANDARD,
    });
    const disableOauth = new ssm.StringParameter(this, "DisableOauth", {
      description: "Disable OAuth for Cognito",
      parameterName: `${ns}DisableOauth`,
      stringValue: "false",
      tier: ssm.ParameterTier.STANDARD,
    });
    const chainlitUrl = new ssm.StringParameter(this, "ChainlitUrl", {
      description: "Chainlit URL, This is important for the app on ECS",
      parameterName: `${ns}ChainlitUrl`,
      stringValue: props.httpApi.apiEndpoint,
      tier: ssm.ParameterTier.STANDARD,
    });

    return {
      appRegion,
      historyTableName,
      chainlitAuthSecret,
      tavilyApiKey,
      disableOauth,
      chainlitUrl,
      cognitoClientId,
      cognitoClientSecret,
    };
  }
}
