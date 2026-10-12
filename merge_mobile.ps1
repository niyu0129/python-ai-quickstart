# 一键合并手机版文件（生成单个合集文件，方便发到手机）
#
# 用法（任选）：
#     1) 双击同目录下的「merge_mobile.bat」
#     2) PowerShell 里执行： powershell -ExecutionPolicy Bypass -File .\merge_mobile.ps1
#
# 说明：本文件以 UTF-8 with BOM 保存，Windows PowerShell 5.1 才能正确识别中文。

$ErrorActionPreference = "Stop"

$root = Join-Path $PSScriptRoot "mobile"
$out  = Join-Path $PSScriptRoot "手机版_全套合集.md"

if (-not (Test-Path $root)) {
    Write-Host "找不到 mobile 目录：$root" -ForegroundColor Red
    exit 1
}

# 合集里的排列顺序（流程表在前，速查和卡片在后）
$order = @(
    "手机版_学习流程表.md",
    "手机版_阶段流程表.md",
    "手机版_项目开发流程表.md",
    "手机版_14天速成计划.md",
    "手机版_每日打卡.md",
    "手机版_Python速查.md",
    "手机版_AI应用速查.md",
    "手机版_背诵卡.md"
)

$sb = New-Object System.Text.StringBuilder
$nl = [Environment]::NewLine

function Add-Line([string]$text) {
    [void]$script:sb.Append($text)
    [void]$script:sb.Append($nl)
}

# ---------- 封面 ----------
Add-Line "# 📱 Python → AI 应用开发 · 手机版全套"
Add-Line ""
Add-Line ("> 生成时间：" + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
Add-Line "> 内容：8 份手机版文档合并成一个文件，方便一次性发到手机。"
Add-Line ""
Add-Line "## 目录"
Add-Line ""

$i = 1
foreach ($name in $order) {
    if (Test-Path (Join-Path $root $name)) {
        Add-Line ("$i. " + $name)
        $i++
    }
}
Add-Line ""
Add-Line "---"
Add-Line ""
Add-Line "> 💡 手机上看时用**搜索**定位（搜「RAG」「字典」「背诵」），不要从头往下翻。"
Add-Line ""

# ---------- 正文 ----------
foreach ($name in $order) {
    $path = Join-Path $root $name
    if (-not (Test-Path $path)) {
        Write-Host "跳过（不存在）：$name" -ForegroundColor Yellow
        continue
    }

    Add-Line ""
    Add-Line ""
    Add-Line ("<!-- ==================== $name ==================== -->")
    Add-Line ""
    Add-Line ("# 【$name】")
    Add-Line ""

    $lines = [System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::UTF8)
    # 去掉原文件第一行的一级标题，避免出现两个 H1
    if ($lines.Count -gt 1 -and $lines[0].StartsWith("# ")) {
        $lines = $lines[1..($lines.Count - 1)]
    }
    Add-Line (($lines -join $nl).Trim())
    Add-Line ""
    Add-Line "---"

    Write-Host "已合并：$name" -ForegroundColor Green
}

[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))

$file = Get-Item $out
$sizeKB = [math]::Round($file.Length / 1KB, 1)
$lineCount = ([System.IO.File]::ReadAllLines($out)).Count

Write-Host ""
Write-Host "✅ 合并完成" -ForegroundColor Cyan
Write-Host ("   文件：" + $out)
Write-Host ("   大小：" + $sizeKB + " KB")
Write-Host ("   行数：" + $lineCount)
Write-Host ""
Write-Host "下一步：把这个文件拖进微信「文件传输助手」，手机上点开即可。" -ForegroundColor Cyan
