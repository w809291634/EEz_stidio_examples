' run_sim_silent.vbs —— 隐藏 cmd 黑框启动 PC 仿真（只显示 SDL 窗口）
' 用法：双击本文件；要构建日志/自证测试时仍用 run_sim.bat。
Option Explicit
Dim fso, sh, dir, bat
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
bat = dir & "\run_sim.bat"
sh.CurrentDirectory = dir
' 0 = 隐藏窗口；False = 不等待（构建在后台完成，随后自动弹 SDL 窗口）
sh.Run "cmd /c """ & bat & """", 0, False
