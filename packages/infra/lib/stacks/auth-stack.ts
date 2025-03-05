import * as cdk from "aws-cdk-lib";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as apigw from "aws-cdk-lib/aws-apigatewayv2";
import * as ssm from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";

interface IProps extends cdk.StackProps {
  readonly httpApi: apigw.IHttpApi;
  readonly callbackUrls: string[];
}

export class AuthStack extends cdk.Stack {
  public readonly userPool: cognito.IUserPool;
  public readonly userPoolClient: cognito.IUserPoolClient;
  public readonly cognitoDomain: ssm.IStringParameter;

  constructor(scope: Construct, id: string, props: IProps) {
    super(scope, id, props);

    const ns = this.node.tryGetContext("ns") as string;

    // setup cognito user pool
    this.userPool = this.newUserPool();
    const domain = this.newCognitoDomain(this.userPool);
    this.cognitoDomain = new ssm.StringParameter(this, "CognitoDomainName", {
      description: "Cognito domain name",
      parameterName: `${ns}CognitoDomainName`,
      stringValue: domain.baseUrl().replace("https://", ""), // Use the Cognito domain from Cognito (without https://),
      tier: ssm.ParameterTier.STANDARD,
    });

    // setup cognito user pool client for Chainlit App
    this.userPoolClient = this.newAlpsAppClient(
      this.userPool,
      props.httpApi,
      props.callbackUrls
    );
  }

  private newUserPool(): cognito.UserPool {
    const ns = this.node.tryGetContext("ns") as string;
    const isProd = this.node.tryGetContext("isProd") as boolean;

    const userPool = new cognito.UserPool(this, "UserPool", {
      userPoolName: `${ns}UserPool`,
      mfa: cognito.Mfa.REQUIRED,
      mfaMessage:
        "Thank you for using ALPS Writer. {username}\n\nHere is your temporary password: {####}",
      mfaSecondFactor: {
        email: false,
        sms: false,
        otp: true,
      },
      selfSignUpEnabled: false,
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      removalPolicy: isProd
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
    });
    return userPool;
  }

  private newCognitoDomain(
    userPool: cognito.IUserPool
  ): cognito.UserPoolDomain {
    const ns = this.node.tryGetContext("ns") as string;
    const domain = new cognito.UserPoolDomain(this, `UserPoolDomain`, {
      userPool,
      cognitoDomain: {
        domainPrefix: `${ns.toLowerCase()}-alps-app-${
          cdk.Stack.of(this).account
        }`,
      },
      managedLoginVersion: cognito.ManagedLoginVersion.NEWER_MANAGED_LOGIN,
    });

    new cdk.CfnOutput(this, "UserPoolDomainName", {
      value: domain.domainName,
    });
    return domain;
  }

  private newAlpsAppClient(
    userPool: cognito.IUserPool,
    httpApi: apigw.IHttpApi,
    callbackUrls: string[]
  ): cognito.UserPoolClient {
    const ns: string = this.node.tryGetContext("ns") as string;

    const CALLBACK_SUFFIX = "auth/oauth/aws-cognito/callback";
    return new cognito.UserPoolClient(this, "AlpsAppClient", {
      userPool,
      userPoolClientName: `${ns}AlpsAppClient`,
      authFlows: {
        adminUserPassword: true,
        userSrp: true,
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.PHONE,
          cognito.OAuthScope.PROFILE,
        ],
        callbackUrls: [
          `${httpApi.apiEndpoint}/${CALLBACK_SUFFIX}`,
          ...callbackUrls,
        ],
      },
      generateSecret: true,
      preventUserExistenceErrors: true,
      idTokenValidity: cdk.Duration.days(1),
      refreshTokenValidity: cdk.Duration.days(30),
      accessTokenValidity: cdk.Duration.hours(12),
      supportedIdentityProviders: [
        cognito.UserPoolClientIdentityProvider.COGNITO,
      ],
    });
  }
}
