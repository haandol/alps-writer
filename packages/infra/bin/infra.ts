import * as cdk from "aws-cdk-lib";
import { AwsPrototypingChecks, PDKNag } from "@aws/pdk/pdk-nag";

import { Config } from "../config/loader";
import { VpcStack } from "../lib/stacks/vpc-stack";
import { AuthStack } from "../lib/stacks/auth-stack";
import { CommonAppStack } from "../lib/stacks/common-app-stack";
import { AlpsAppStack } from "../lib/stacks/alps-app-stack";

const app = PDKNag.app({
  nagPacks: [new AwsPrototypingChecks()],
  context: {
    ns: Config.app.ns,
    stage: Config.app.stage,
    isProd: Config.app.stage.toLowerCase() === "prod",
  },
});

const vpcStack = new VpcStack(app, `${Config.app.ns}Vpc`, {
  vpcId: Config.vpc?.vpcId,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

const commonAppStack = new CommonAppStack(app, `${Config.app.ns}CommonApp`, {
  vpc: vpcStack.vpc,
  tableName: Config.chatbot.tableName,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
commonAppStack.addDependency(vpcStack);

const authStack = new AuthStack(app, `${Config.app.ns}Auth`, {
  httpApi: commonAppStack.httpApi,
  callbackUrls: Config.auth.callbackUrls,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
authStack.addDependency(commonAppStack);

const alpsAppStack = new AlpsAppStack(app, `${Config.app.ns}AlpsApp`, {
  vpc: vpcStack.vpc,
  userPool: authStack.userPool,
  cognitoDomain: authStack.cognitoDomain,
  httpApi: commonAppStack.httpApi,
  vpcLink: commonAppStack.vpcLink,
  cluster: commonAppStack.cluster,
  loadBalancer: commonAppStack.loadBalancer,
  userPoolClient: authStack.userPoolClient,
  appRegion: process.env.CDK_DEFAULT_REGION as string,
  bedrockModelId: Config.chatbot.bedrockModelId,
  historyTableName: Config.chatbot.tableName,
  tavilyApiKey: Config.external.web.tavilyApiKey,
  callbackUrls: Config.auth.callbackUrls,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
alpsAppStack.addDependency(authStack);

const tags = cdk.Tags.of(app);
tags.add("namespace", Config.app.ns);
tags.add("stage", Config.app.stage);

app.synth();
