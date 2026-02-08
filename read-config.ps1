# 读取 WebRPAConfig.json 配置文件
param(
    [string]$Key
)

$configPath = Join-Path $PSScriptRoot "WebRPAConfig.json"

try {
    if (Test-Path $configPath) {
        $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        
        switch ($Key) {
            "backend.port" { Write-Output $config.backend.port }
            "frontend.port" { Write-Output $config.frontend.port }
            "frameworkHub.port" { Write-Output $config.frameworkHub.port }
            default { Write-Output "" }
        }
    } else {
        # 配置文件不存在，返回默认值
        switch ($Key) {
            "backend.port" { Write-Output "8000" }
            "frontend.port" { Write-Output "5173" }
            "frameworkHub.port" { Write-Output "3000" }
            default { Write-Output "" }
        }
    }
} catch {
    # 读取失败，返回默认值
    switch ($Key) {
        "backend.port" { Write-Output "8000" }
        "frontend.port" { Write-Output "5173" }
        "frameworkHub.port" { Write-Output "3000" }
        default { Write-Output "" }
    }
}
