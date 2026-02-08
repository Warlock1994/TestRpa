# 简化版禁用快速编辑模式
$code = @"
using System;
using System.Runtime.InteropServices;

public class ConsoleHelper {
    private const int STD_INPUT_HANDLE = -10;
    private const uint ENABLE_QUICK_EDIT_MODE = 0x0040;
    private const uint ENABLE_EXTENDED_FLAGS = 0x0080;

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr GetStdHandle(int nStdHandle);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint lpMode);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode);

    public static bool DisableQuickEditMode() {
        IntPtr consoleHandle = GetStdHandle(STD_INPUT_HANDLE);
        uint consoleMode;
        
        if (!GetConsoleMode(consoleHandle, out consoleMode)) {
            return false;
        }

        consoleMode &= ~ENABLE_QUICK_EDIT_MODE;
        consoleMode |= ENABLE_EXTENDED_FLAGS;

        return SetConsoleMode(consoleHandle, consoleMode);
    }
}
"@

Add-Type -TypeDefinition $code
[ConsoleHelper]::DisableQuickEditMode() | Out-Null
