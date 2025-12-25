Set ws = CreateObject("WScript.Shell")
Set args = WScript.Arguments

' 获取当前脚本所在目录
currentDirectory = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' 切换到脚本所在目录
ws.CurrentDirectory = currentDirectory

' 构建命令行参数
commandLine = "FaustLauncher.exe -launcher"

' 运行主程序（隐藏控制台窗口）
ws.Run commandLine, 0, False