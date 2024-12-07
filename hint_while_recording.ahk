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

Hotkey "~" chineseKey, chineseVoice
Hotkey "~" englishKey chineseKey, englishVoice
Hotkey "~*" chineseKey " Up", BttRemove

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

chineseVoice(ThisHotkey) {
    Hotkey "~" chineseKey, "Off" ; 关闭快捷键功能,以免重复触发
    Hotkey "~" englishKey chineseKey, "Off"
    if hwnd := GetCaretPosEx(&x, &y, &w, &h, true) {
        ; 能够获取到文本光标时，提示信息在光标位置，且x坐标向右偏移5
        x := x + 5
    }
    else {
        ; 获取不到文本光标时，提示信息在当前窗口的位置
        WinGetPos &X, &Y, &W, &H, "A"
        x := X + W * 0.25
        y := Y + H * 0.7
    }
    if enableBTT
        btt(cnTxt, x, y - 3, 20, OwnStyle1, { Transparent: 255 }) ;btt的主要函数, 透明度(Transparent 0 - 255)
    else
        ToolTip(cnTxt, x, y) ; 提示信息内容
    KeyWait(chineseKey)
    return
}

englishVoice(ThisHotkey) {
    Hotkey "~" chineseKey, "Off" ; 关闭快捷键功能,以免重复触发
    Hotkey "~" englishKey chineseKey, "Off"
    if hwnd := GetCaretPosEx(&x, &y, &w, &h, true) {
        ; 能够获取到文本光标时，提示信息在光标位置，且x坐标向右偏移5
        x := x + 5
    }
    else {
        ; 获取不到文本光标时，提示信息在当前窗口的位置
        WinGetPos &X, &Y, &W, &H, "A"
        x := X + W * 0.25
        y := Y + H * 0.7
    }
    if enableBTT
        btt(enTxt, x, y - 3, 20, OwnStyle2, { Transparent: 255 }) ;btt的主要函数, 透明度(Transparent 0 - 255)
    else
        ToolTip(enTxt, x, y) ; 提示信息内容
    KeyWait(chineseKey)
    return
}

BttRemove(ThisHotkey) {
    Sleep 50
    if enableBTT
        btt(, , , 20)
    else
        ToolTip()
    SetTimer EnableShortcutKeys, hotkeyTurnOnDelay ; 改善在游戏中错误启动提示的情况: 延迟`hotkeyTurnOnDelay毫秒`后重新启用热键
}

EnableShortcutKeys(*) {
    Hotkey "~" chineseKey, "On" ; 恢复快捷键功能
    Hotkey "~" englishKey chineseKey, "On"
}

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
}