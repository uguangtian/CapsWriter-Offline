; 为原来的脚本提供了另一种显示方式(使用BeautifulToolTip库),并且提供修改配置的功能,在这个`hint_while_recording.ini`文件修改。
; 使用BeautifulToolTip库显示的好处是不会改变焦点,从而退出全屏幕模式(需要在`config.py` 的 `hint_while_recording_at_cursor_position = False`配合使用)。另外比较漂亮。坏处是增加了30MB记忆体的占用。
; 改善在游戏中错误启动提示的情况: 延迟`hotkeyTurnOnDelay毫秒`后重新启用热键
; hint_while_recording:
; Author:[H1DDENADM1N](https://github.com/H1DDENADM1N/CapsWriter-Offline)
; Contributor: [JoanthanWu](https://github.com/JoanthanWu/CapsWriter-Offline)
; 第三方库`BeautifulToolTip`:
; Author: [telppa](https://github.com/telppa/BeautifulToolTip)
; Contributor: [liuyi91](https://github.com/liuyi91/ahkv2lib-)
; Contributor: [thqby](https://github.com/thqby)

#Requires AutoHotkey v2.0
#SingleInstance Force
#Include BTTv2.ahk
#Include GetCaretPosEx.ahk
InstallKeybdHook
InstallMouseHook
TraySetIcon(A_ScriptDir "\assets\hint_while_recording.ico", 1)
CoordMode("ToolTip", "Screen")

IniFile := A_ScriptDir "\hint_while_recording.ini"
if !FileExist(IniFile) {
    DefaultIni()
}
ReadIni()

global keyPressed := False
global lastTimePressed := 0
global lastTimeReleased := 0
global isShortDuration := False
global threshold := 300
global is_microphone_in_use := False
global hold_mode := False


Hotkey "~" chineseKey, chineseVoice_down
Hotkey "~" chineseKey " Up", chineseVoice_up
; Hotkey "~" englishKey, englishVoice_down
; Hotkey "~" englishKey " Up", englishVoice_up

OnMessage 0x5555, MsgMonitor
Persistent

MsgMonitor(wParam, lParam, msg, *)
{
    ; Since returning quickly is often important, it is better to use ToolTip than
    ; something like MsgBox that would prevent the callback from finishing:
    ; ToolTip "Message " msg " arrived:`nis_microphone_in_use: " wParam "`nhold_mode: " lParam
    global is_microphone_in_use, hold_mode
    is_microphone_in_use := wParam
    hold_mode := lParam
    if !is_microphone_in_use {
        btt(, , , 20)
    }
}

OwnStyle1 := { TextColorLinearGradientStart: cnTxtClolorA        ; ARGB
    , TextColorLinearGradientEnd: cnTxtClolorB         ; ARGB
    , TextColorLinearGradientAngle: 0                 ; Mode=8 Angle 0(L to R) 90(U to D) 180(R to L) 270(D to U)
    , TextColorLinearGradientMode: 2                  ; Mode=4 Angle 0(L to R) 90(D to U), Range 1-8.
    , BackgroundColor: 0x00ffffff
    , FontSize: cnTxtFontSize
    , FontRender: 4
    , FontStyle: "Bold" }
OwnStyle2 := { TextColorLinearGradientStart: enTxtClolorA        ; ARGB
    , TextColorLinearGradientEnd: enTxtClolorB         ; ARGB
    , TextColorLinearGradientAngle: 0                 ; Mode=8 Angle 0(L to R) 90(U to D) 180(R to L) 270(D to U)
    , TextColorLinearGradientMode: 2                  ; Mode=4 Angle 0(L to R) 90(D to U), Range 1-8.
    , BackgroundColor: 0x00ffffff
    , FontSize: enTxtFontSize
    , FontRender: 4
    , FontStyle: "Bold" }

chineseVoice_down(*) {
    global keyPressed, lastTimePressed, isShortDuration, threshold, is_microphone_in_use, hold_mode
    if !keyPressed {
        lastTimePressed := A_TickCount
        keyPressed := True
    }
    if hold_mode {
        ; 在doNotShowHintList中的程序将不会显示“语音输入中”的提示
        exe_name := ""
        try {
            exe_name := ProcessGetName(WinGetPID("A"))
            DllCall("SetThreadDpiAwarenessContext", "ptr", -2, "ptr")
            ; ToolTip(exe_name)
        }
        if (InStr(doNotShowHintList, ":" exe_name ":")) {
            return
        }

        if is_microphone_in_use and hwnd := GetCaretPosEx(&x, &y, &w, &h) { ;麦克风启用
            if hwnd := GetCaretPosEx(&x, &y, &w, &h) { ;能够获取到文本光标时，提示信息在输入光标位置，且x坐标向右偏移5
                x := x + 5
            } else { ;获取不到文本光标位置，提示信息在鼠标光标位置
                CoordMode "Mouse", "Screen"  ; 确保MouseGetPos使用的是屏幕坐标
                MouseGetPos(&x, &y)  ; 获取鼠标的当前位置，并将X坐标存储在变量x中，Y坐标存储在变量y中
            }
            btt(cnTxt, x, y - 3, 20, OwnStyle1, { Transparent: 255 })
        }
    } else {
        ToolTip "单击模式的代码懒得写了"
    }
}
chineseVoice_up(*) {
    global keyPressed, lastTimePressed, lastTimeReleased, isShortDuration, threshold, is_microphone_in_use, hold_mode
    keyPressed := False
    lastTimeReleased := A_TickCount
    isShortDuration := (A_TickCount - lastTimePressed < threshold) ? True : False
    if hold_mode {
        btt(, , , 20)
    }
    else {
        ToolTip "单击模式的代码懒得写了"
    }
}
; englishVoice_down(*) {
;     Hotkey "~" chineseKey englishKey, "Off" ; 关闭快捷键功能,以免重复触发
; }

DefaultIni() {
    IniWrite("1", IniFile, "BeautifulToolTip", "enableBTT")
    IniWrite("-67", IniFile, "BeautifulToolTip", "hotkeyTurnOnDelay")
    IniWrite("✦语音输入中‧‧‧", IniFile, "ShowText", "cnTxt")
    IniWrite("✦VoiceTrans‧‧‧", IniFile, "ShowText", "enTxt")
    IniWrite("CapsLock", IniFile, "Hotkey", "chineseKey")
    IniWrite("+", IniFile, "Hotkey", "englishKey")
    IniWrite("0xFFCC7A00", IniFile, "Txt", "cnTxtClolorA")
    IniWrite("0xFFFFDF80", IniFile, "Txt", "cnTxtClolorB")
    IniWrite("16", IniFile, "Txt", "cnTxtFontSize")
    IniWrite("0xFF1A1AFF", IniFile, "Txt", "enTxtClolorA")
    IniWrite("0xFF6666FF", IniFile, "Txt", "enTxtClolorB")
    IniWrite("16", IniFile, "Txt", "enTxtFontSize")
    IniWrite("在hintAtCursorPositionList中的程序将不会把“语音输入中”的提示显示在文本光标位置，而是显示在鼠标光标的位置", IniFile, "List", "Comment1")
    IniWrite(":StartMenuExperienceHost.exe:wetype_update.exe:AnLink.exe:wps.exe:PotPlayer.exe:PotPlayer64.exe:PotPlayerMini.exe:PotPlayerMini64.exe:HBuilderX.exe:ShareX.exe:clipdiary-portable.exe:", IniFile, "List", "hintAtCursorPositionList")
    IniWrite("在doNotShowHintList中的程序将不会显示“语音输入中”的提示", IniFile, "List", "Comment2")
    IniWrite(":PotPlayer.exe:PotPlayer64.exe:PotPlayerMini.exe:PotPlayerMini64.exe:", IniFile, "List", "doNotShowHintList")
}

ReadIni() {
    global enableBTT := IniRead(IniFile, "BeautifulToolTip", "enableBTT")
    global hotkeyTurnOnDelay := IniRead(IniFile, "BeautifulToolTip", "hotkeyTurnOnDelay")
    global cnTxt := IniRead(IniFile, "ShowText", "cnTxt")
    global enTxt := IniRead(IniFile, "ShowText", "enTxt")
    global chineseKey := IniRead(IniFile, "Hotkey", "chineseKey")
    global englishKey := IniRead(IniFile, "Hotkey", "englishKey")
    global cnTxtClolorA := IniRead(IniFile, "Txt", "cnTxtClolorA")
    global cnTxtClolorB := IniRead(IniFile, "Txt", "cnTxtClolorB")
    global cnTxtFontSize := IniRead(IniFile, "Txt", "cnTxtFontSize")
    global enTxtClolorA := IniRead(IniFile, "Txt", "enTxtClolorA")
    global enTxtClolorB := IniRead(IniFile, "Txt", "enTxtClolorB")
    global enTxtFontSize := IniRead(IniFile, "Txt", "enTxtFontSize")
    global doNotShowHintList := IniRead(IniFile, "List", "doNotShowHintList")
}