import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { LogGroup, RetentionDays } from "aws-cdk-lib/aws-logs";
import * as nag from "cdk-nag";
import { Construct, IConstruct } from "constructs";

interface IProps extends cdk.StackProps {
  vpcId?: string;
}

export class VpcStack extends cdk.Stack {
  readonly vpc: ec2.IVpc;

  constructor(scope: Construct, id: string, props: IProps) {
    super(scope, id, props);

    if (props.vpcId) {
      const vpc = ec2.Vpc.fromLookup(this, "Vpc", {
        vpcId: props.vpcId,
      });

      this.vpc = vpc;
    } else {
      const vpc = this.createVpc();
      const securityGroup = this.createVpcEndpointSecurityGroup(vpc);
      this.createVpcEndpoints(vpc, securityGroup);
      this.vpc = vpc;
    }
  }

  private createVpc(): ec2.Vpc {
    const ns = this.node.tryGetContext("ns") as string;

    const cloudWatchLogs = new LogGroup(this, "FlowLogs", {
      retention: RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    return new ec2.Vpc(this, "Vpc", {
      vpcName: `${ns.toLowerCase()}`,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: "ingress",
          subnetType: ec2.SubnetType.PUBLIC,
          mapPublicIpOnLaunch: false,
        },
        {
          cidrMask: 24,
          name: "egress",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          cidrMask: 24,
          name: "isolated",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
      flowLogs: {
        cloudwatch: {
          destination: ec2.FlowLogDestination.toCloudWatchLogs(cloudWatchLogs),
          trafficType: ec2.FlowLogTrafficType.ALL,
        },
      },
    });
  }

  private createVpcEndpoints(vpc: ec2.IVpc, securityGroup: ec2.ISecurityGroup) {
    vpc.addGatewayEndpoint("S3VpcE", {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });
    vpc.addGatewayEndpoint("DdbVpcE", {
      service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
    });
    const endpoints: IConstruct[] = [
      vpc.addInterfaceEndpoint("BedrockVpcE", {
        service: ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
        securityGroups: [securityGroup],
      }),
      // https://docs.aws.amazon.com/AmazonECS/latest/developerguide/vpc-endpoints.html
      // https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-network.html
      vpc.addInterfaceEndpoint("EcrApiVpcE", {
        service: ec2.InterfaceVpcEndpointAwsService.ECR,
        securityGroups: [securityGroup],
      }),
      vpc.addInterfaceEndpoint("EcrDockerVpcE", {
        service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
        securityGroups: [securityGroup],
      }),
      vpc.addInterfaceEndpoint("EcsEndpointVpcE", {
        service: ec2.InterfaceVpcEndpointAwsService.ECS,
        securityGroups: [securityGroup],
      }),
      vpc.addInterfaceEndpoint("EcsAgentVpcE", {
        service: ec2.InterfaceVpcEndpointAwsService.ECS_AGENT,
        securityGroups: [securityGroup],
      }),
      vpc.addInterfaceEndpoint("EcsTelemetryVpcE", {
        service: ec2.InterfaceVpcEndpointAwsService.ECS_TELEMETRY,
        securityGroups: [securityGroup],
      }),
    ];
    console.log(endpoints);
  }

  private createVpcEndpointSecurityGroup(vpc: ec2.IVpc): ec2.SecurityGroup {
    const securityGroup = new ec2.SecurityGroup(
      this,
      "vpcEndpointSecurityGroup",
      {
        vpc: vpc,
      }
    );
    securityGroup.addIngressRule(
      ec2.Peer.ipv4(vpc.vpcCidrBlock),
      ec2.Port.tcp(443),
      "Allow internal access for several VPC Endpoint"
    );
    nag.NagSuppressions.addResourceSuppressions(
      securityGroup,
      [
        {
          id: "AwsPrototyping-EC2RestrictedCommonPorts",
          reason: "VPC Endpoint uses common ports",
        },
        {
          id: "AwsPrototyping-EC2RestrictedInbound",
          reason: "PDK-NAG BUG? security group does not allow inbound access.",
        },
        {
          id: "AwsPrototyping-EC2RestrictedSSH",
          reason: "PDK-NAG BUG? security group does not allow SSH port access.",
        },
      ],
      true
    );
    return securityGroup;
  }
}
