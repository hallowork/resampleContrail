# PowerShell脚本 - 模拟Slurm任务数组
# 用于在Windows上测试任务划分逻辑

param(
    [int]$Year = 2013,
    [int]$StartDOY = 1,
    [int]$EndDOY = 4,
    [int]$MaxParallel = 2,
    [string]$PythonExe = "C:\Users\wuch\miniconda3\envs\wchShap\python.exe"
)

Write-Host "========================================"
Write-Host "Slurm任务数组模拟测试"
Write-Host "========================================"
Write-Host "年份: $Year"
Write-Host "日期范围: $StartDOY - $EndDOY"
Write-Host "最大并行数: $MaxParallel"
Write-Host "Python路径: $PythonExe"
Write-Host "========================================"

# 创建任务列表
$tasks = @()
for ($doy = $StartDOY; $doy -le $EndDOY; $doy++) {
    $tasks += @{
        TaskID = $doy - 1  # 模拟SLURM_ARRAY_TASK_ID (从0开始)
        Year = $Year
        DOY = $doy
        Date = "{0}{1:000}" -f $Year, $doy
    }
}

Write-Host "创建了 $($tasks.Count) 个任务"

# 创建结果目录
$resultsDir = ".\test_results"
if (!(Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir
}

# 模拟并行执行
$jobs = @()
$completed = 0
$failed = 0

foreach ($task in $tasks) {
    # 控制并行数量
    while ($jobs.Count -ge $MaxParallel) {
        $jobs = $jobs | Where-Object { $_.State -eq "Running" }
        Start-Sleep -Seconds 1
    }
    
    Write-Host "启动任务: 日期 $($task.Date) (TaskID: $($task.TaskID))"
    
    # 设置环境变量并启动任务
    $scriptBlock = {
        param($pythonExe, $taskId, $year)
        
        # 设置模拟的Slurm环境变量
        $env:SLURM_ARRAY_TASK_ID = $taskId
        $env:PROCESS_YEAR = $year
        
        # 执行Python脚本
        & $pythonExe "process_single_date.py" --task-id $taskId --year $year
        
        return @{
            TaskID = $taskId
            Year = $year
            ExitCode = $LASTEXITCODE
            Output = $output
        }
    }
    
    # 启动后台任务
    $job = Start-Job -ScriptBlock $scriptBlock -ArgumentList $PythonExe, $task.TaskID, $task.Year
    $jobs += $job
}

# 等待所有任务完成
Write-Host "等待所有任务完成..."
$jobs | Wait-Job | ForEach-Object {
    $result = Receive-Job $_
    Remove-Job $_
    
    if ($result.ExitCode -eq 0) {
        Write-Host "任务 $($result.TaskID) (年份 $($result.Year)) 成功完成" -ForegroundColor Green
        $completed++
    } else {
        Write-Host "任务 $($result.TaskID) (年份 $($result.Year)) 执行失败" -ForegroundColor Red
        $failed++
    }
}

# 输出最终统计
Write-Host "========================================"
Write-Host "执行完成统计:"
Write-Host "  总任务数: $($tasks.Count)"
Write-Host "  成功完成: $completed"
Write-Host "  执行失败: $failed"
Write-Host "  成功率: $(($completed / $tasks.Count * 100).ToString('F1'))%"
Write-Host "========================================"

# 检查日志文件
$logDir = ".\output\logs"
if (Test-Path $logDir) {
    $logFiles = Get-ChildItem $logDir -Filter "contrail_*.log" | Sort-Object LastWriteTime -Descending
    Write-Host "生成的日志文件:"
    $logFiles | ForEach-Object {
        Write-Host "  $($_.Name) ($(($_.Length/1KB).ToString('F1'))KB)"
    }
}
