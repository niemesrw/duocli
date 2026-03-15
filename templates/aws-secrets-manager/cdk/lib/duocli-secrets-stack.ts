import * as cdk from "aws-cdk-lib";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";

export class DuocliSecretsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const readerArns = this.node.tryGetContext("readerArns") as string[] | undefined;

    // Duo Admin API credentials stored as a JSON secret
    const secret = new secretsmanager.Secret(this, "DuoAdminApiSecret", {
      secretName: "duocli/duo-admin-api",
      description: "Duo Admin API credentials for duocli",
      secretStringValue: cdk.SecretValue.unsafePlainText(
        JSON.stringify({
          DUO_IKEY: "PLACEHOLDER",
          DUO_SKEY: "PLACEHOLDER",
          DUO_HOST: "PLACEHOLDER",
        })
      ),
    });

    // Grant read access to specified IAM user/role ARNs
    if (readerArns && readerArns.length > 0) {
      for (const arn of readerArns) {
        secret.grantRead(new iam.ArnPrincipal(arn));
      }
    }

    new cdk.CfnOutput(this, "SecretArn", {
      value: secret.secretArn,
      description: "ARN of the Duo Admin API secret",
    });

    new cdk.CfnOutput(this, "SecretName", {
      value: secret.secretName,
      description: "Name of the Duo Admin API secret",
    });
  }
}
