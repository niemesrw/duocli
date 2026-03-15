#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { DuocliSecretsStack } from "../lib/duocli-secrets-stack";

const app = new cdk.App();

new DuocliSecretsStack(app, "DuocliSecretsStack", {
  env: {
    account: app.node.tryGetContext("account") || process.env.CDK_DEFAULT_ACCOUNT,
    region: app.node.tryGetContext("region") || process.env.CDK_DEFAULT_REGION,
  },
});
