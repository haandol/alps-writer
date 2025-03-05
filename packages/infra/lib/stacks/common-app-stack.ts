import * as cdk from "aws-cdk-lib";
import * as apigw from "aws-cdk-lib/aws-apigatewayv2";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import { Construct } from "constructs";
import { ReverseProxy } from "../constructs/reverse-proxy";

interface IProps extends cdk.StackProps {
  readonly vpc: ec2.IVpc;
  readonly tableName: string;
  readonly tavilyApiKey: string;
}

export class CommonAppStack extends cdk.Stack {
  // reverse proxy
  readonly httpApi: apigw.IHttpApi;
  readonly vpcLink: apigw.IVpcLink;
  readonly securityGroup: ec2.ISecurityGroup;
  // chat app
  readonly historyTable: dynamodb.ITable;
  // ecs fargate service
  readonly cluster: ecs.ICluster;
  readonly loadBalancer: elbv2.IApplicationLoadBalancer;

  constructor(scope: Construct, id: string, props: IProps) {
    super(scope, id, props);

    // setup reverse proxy
    const reverseProxy = new ReverseProxy(this, "ReverseProxy", {
      vpc: props.vpc,
    });
    this.httpApi = reverseProxy.httpApi;
    this.vpcLink = reverseProxy.vpcLink;
    this.securityGroup = reverseProxy.securityGroup;

    // setup chat history for chainlit app
    this.historyTable = this.newChatHistoryTable(props.tableName);

    // setup ECS fargate service
    this.cluster = this.newECSCluster(props.vpc);
    this.loadBalancer = this.newALB(props.vpc);
  }

  private newECSCluster(vpc: ec2.IVpc): ecs.Cluster {
    const ns: string = this.node.tryGetContext("ns") as string;
    const cluster = new ecs.Cluster(this, "Cluster", {
      clusterName: ns.toLowerCase(),
      vpc,
      defaultCloudMapNamespace: {
        name: ns.toLowerCase(),
      },
      enableFargateCapacityProviders: true,
      containerInsights: true,
    });
    return cluster;
  }

  private newChatHistoryTable(tableName: string): dynamodb.Table {
    const isProd = this.node.tryGetContext("isProd") as boolean;

    const table = new dynamodb.Table(this, "ChatHistoryTable", {
      tableName,
      partitionKey: {
        name: "PK",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "SK",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: isProd
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
    });
    // for chainlit chatbot
    table.addGlobalSecondaryIndex({
      indexName: "UserThread",
      partitionKey: {
        name: "UserThreadPK",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "UserThreadSK",
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.INCLUDE,
      nonKeyAttributes: ["id", "name"],
    });
    // for general purpose
    table.addGlobalSecondaryIndex({
      indexName: "GSI1",
      partitionKey: {
        name: "GS1PK",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "GS1SK",
        type: dynamodb.AttributeType.STRING,
      },
    });

    new cdk.CfnOutput(this, "ChatHistoryTableOutput", {
      value: table.tableName,
    });

    return table;
  }

  private newALB(vpc: ec2.IVpc): elbv2.IApplicationLoadBalancer {
    const ns = this.node.tryGetContext("ns") as string;
    return new elbv2.ApplicationLoadBalancer(this, "ALB", {
      loadBalancerName: `${ns}CommonAppALB`,
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroup: this.securityGroup,
    });
  }
}
