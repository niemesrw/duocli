@description('Name of the Key Vault')
param vaultName string

@description('Azure region for the Key Vault')
param location string = resourceGroup().location

@description('Object IDs of users/groups who can read the Duo secret')
param secretReaderPrincipalIds array

@description('Object ID of the admin who can manage secrets')
@secure()
param secretAdminPrincipalId string

@description('Duo Admin API credentials as JSON string: {"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}')
@secure()
param duoSecretValue string

// Key Vault Secrets User — read secret values
var secretUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

// Key Vault Secrets Officer — manage secrets (create, update, delete)
var secretOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
  }
}

resource duoSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'duo-admin-api'
  properties: {
    value: duoSecretValue
    contentType: 'application/json'
  }
}

// Grant each reader principal the Secrets User role scoped to the vault
resource readerRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for (principalId, i) in secretReaderPrincipalIds: {
    name: guid(vault.id, principalId, secretUserRoleId)
    scope: vault
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretUserRoleId)
      principalId: principalId
      principalType: 'User'
    }
  }
]

// Grant the admin the Secrets Officer role scoped to the vault
resource adminRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, secretAdminPrincipalId, secretOfficerRoleId)
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretOfficerRoleId)
    principalId: secretAdminPrincipalId
    principalType: 'User'
  }
}

output vaultUri string = vault.properties.vaultUri
output vaultName string = vault.name
output secretName string = duoSecret.name
