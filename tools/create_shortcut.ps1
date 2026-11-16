$ErrorActionPreference = 'Stop'
$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'Hot100 训练台.lnk'
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($linkPath)
$sc.TargetPath = 'C:\Users\zhongwei.mo\AppData\Local\Programs\Python\Python312\pythonw.exe'
$sc.Arguments = '"C:\Workspace\leetcode-hot100-trainer\trainer.py" serve --browser'
$sc.WorkingDirectory = 'C:\Workspace\leetcode-hot100-trainer'
$sc.IconLocation = 'C:\Workspace\leetcode-hot100-trainer\assets\hot100.ico,0'
$sc.Description = 'Hot 100 训练台 - 启动本地仪表盘'
$sc.WindowStyle = 1
$sc.Save()
Write-Output ("OK " + $linkPath)
