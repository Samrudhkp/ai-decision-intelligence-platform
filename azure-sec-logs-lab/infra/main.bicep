@description('Event-driven security lab: Blob logs → Event Grid → Function → Blob reports')
param location string = 'eastus'
param resourceGroupName string = 'rg-sec-logs-lab'
param storageAccountName string
param functionAppName string
param failureThreshold int = 5

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

module lab 'lab.bicep' = {
  name: 'sec-logs-lab'
  scope: rg
  params: {
    location: location
    storageAccountName: storageAccountName
    functionAppName: functionAppName
    failureThreshold: failureThreshold
  }
}

output resourceGroup string = rg.name
output storageAccountName string = lab.outputs.storageAccountName
output functionAppName string = lab.outputs.functionAppName
output logsContainer string = lab.outputs.logsContainer
output reportsContainer string = lab.outputs.reportsContainer
output eventSubscriptionName string = lab.outputs.eventSubscriptionName
