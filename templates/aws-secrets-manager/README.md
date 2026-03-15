# AWS Secrets Manager — duocli secret template

Store Duo Admin API credentials in AWS Secrets Manager using CDK. Every `GetSecretValue` call is logged in CloudTrail, giving you an audit trail of who ran duocli and when.

## Prerequisites

- AWS account with CLI access (`aws sso login` or IAM credentials)
- [Node.js](https://nodejs.org/) and npm
- CDK bootstrapped: `npx cdk bootstrap aws://ACCOUNT/REGION`

## Setup

1. Install and deploy:

   ```bash
   chmod +x setup.sh
   ./setup.sh --profile your-profile
   ```

   To grant read access to specific IAM users/roles:

   ```bash
   ./setup.sh --profile your-profile \
     -c 'readerArns=["arn:aws:iam::123456789012:user/alice","arn:aws:iam::123456789012:role/duo-operators"]'
   ```

2. Store your Duo credentials:

   ```bash
   aws secretsmanager put-secret-value \
     --secret-id duocli/duo-admin-api \
     --secret-string '{"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}' \
     --profile your-profile
   ```

## Usage

```bash
export AWS_PROFILE=your-profile
chmod +x wrapper.sh

./wrapper.sh list-apps
./wrapper.sh --human info-summary
./wrapper.sh create-app --name "My App" --type websdk
```

The wrapper fetches credentials from Secrets Manager, exports them as env vars, and execs duocli. Your AWS identity (SSO user, IAM user/role) is recorded in CloudTrail.

## What gets audited

CloudTrail logs a `GetSecretValue` event for every secret access, including:

- **Who** — the IAM principal (SSO user, IAM user, assumed role)
- **When** — timestamp
- **What** — secret ARN
- **Where** — source IP address

View audit logs:

```bash
# Recent Secrets Manager events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
  --max-results 10 \
  --profile your-profile
```

## Rotating credentials

```bash
aws secretsmanager put-secret-value \
  --secret-id duocli/duo-admin-api \
  --secret-string '{"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}' \
  --profile your-profile
```

Previous versions are retained and accessible via version stages.

## Cleanup

```bash
cd cdk && npx cdk destroy --profile your-profile
```

Note: Secrets Manager has a minimum 7-day recovery window before permanent deletion.
