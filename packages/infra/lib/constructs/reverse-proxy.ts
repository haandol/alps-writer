import * as cdk from "aws-cdk-lib";
import * as apigw from "aws-cdk-lib/aws-apigatewayv2";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

interface IProps {
  vpc: ec2.IVpc;
}

export class ReverseProxy extends Construct {
  readonly httpApi: apigw.IHttpApi;
  readonly vpcLink: apigw.IVpcLink;
  readonly securityGroup: ec2.ISecurityGroup;

  constructor(scope: Construct, id: string, props: IProps) {
    super(scope, id);

    const securityGroup = this.createSecurityGroup(props.vpc);
    this.httpApi = this.createHttpApi();
    this.vpcLink = this.createVpcLink(this.httpApi, props.vpc, securityGroup);
  }

  private createSecurityGroup(vpc: ec2.IVpc): ec2.SecurityGroup {
    return new ec2.SecurityGroup(this, "CommonAppSecurityGroup", { vpc });
  }

  private createHttpApi(): apigw.HttpApi {
    const ns = this.node.tryGetContext("ns") as string;
    const api = new apigw.HttpApi(this, "HttpApi", {
      apiName: `${ns}CommonAppApi`,
      corsPreflight: {
        allowOrigins: ["*"],
        allowMethods: [
          apigw.CorsHttpMethod.POST,
          apigw.CorsHttpMethod.GET,
          apigw.CorsHttpMethod.PUT,
          apigw.CorsHttpMethod.DELETE,
          apigw.CorsHttpMethod.OPTIONS,
        ],
        allowHeaders: [
          "Authorization",
          "Content-Type",
          "X-Amzn-Trace-Id",
          "X-Requested-With",
        ],
        allowCredentials: false,
        maxAge: cdk.Duration.hours(1),
      },
    });

    new cdk.CfnOutput(this, "CommonAppHttpApiUrl", {
      value: api.apiEndpoint,
    });

    return api;
  }

  private createVpcLink(
    httpApi: apigw.IHttpApi,
    vpc: ec2.IVpc,
    securityGroup: ec2.ISecurityGroup
  ): apigw.VpcLink {
    return httpApi.addVpcLink({
      vpc,
      securityGroups: [securityGroup],
    });
  }
}
