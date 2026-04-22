# Alibaba Cloud Provisioning Script - Digital FTE
param (
    [string]$AccessKeyId,
    [string]$AccessKeySecret,
    [string]$Region = "cn-hangzhou"
)

Write-Host "Configuring Aliyun CLI..."
./aliyun.exe configure set --profile dte_prod --access-key-id $AccessKeyId --access-key-secret $AccessKeySecret --region $Region

Write-Host "Creating RDS PostgreSQL 14 Instance..."
$rdsResponse = ./aliyun.exe rds CreateDBInstance `
    --Engine PostgreSQL `
    --EngineVersion 14.0 `
    --DBInstanceClass "pg.n2.small.1" `
    --DBInstanceStorage 20 `
    --Category "Basic" `
    --PayType "PayAsYouGo" `
    --RegionId "cn-hangzhou" `
    --InstanceNetworkType "VPC" `
    --VPCId "vpc-bp1x9l74et99dja73v9yk" `
    --VSwitchId "vsw-bp19fnji9nnyy58r3buvt" `
    --ZoneId "cn-hangzhou-h" `
    --DBInstanceNetType "Intranet" `
    --SecurityIPList "0.0.0.0/0"
if ($LASTEXITCODE -ne 0) { Write-Error "RDS Creation Failed"; exit 1 }

$rdsResult = $rdsResponse | ConvertFrom-Json
$instanceId = $rdsResult.DBInstanceId
Write-Host "Instance Created: $instanceId"

Write-Host "Creating Database Account..."
./aliyun.exe rds CreateAccount --DBInstanceId $instanceId --AccountName dte_user --AccountPassword "ProdPass123!" --AccountType Normal

Write-Host "Creating Database 'dte_db'..."
./aliyun.exe rds CreateDatabase --DBInstanceId $instanceId --DBName dte_db --CharacterSetName UTF8

Write-Host "Configuring Whitelist (0.0.0.0/0)..."
./aliyun.exe rds ModifySecurityIps --DBInstanceId $instanceId --SecurityIps "0.0.0.0/0"

Write-Host "RDS Setup Complete. Please wait for instance to finish initializing before running Docker."
