"""系统对话框相关API - 文件/文件夹选择"""
import subprocess
import sys
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class OpenUrlRequest(BaseModel):
    url: str


class FolderSelectRequest(BaseModel):
    title: Optional[str] = "选择文件夹"
    initialDir: Optional[str] = None


class FileSelectRequest(BaseModel):
    title: Optional[str] = "选择文件"
    initialDir: Optional[str] = None
    fileTypes: Optional[list[tuple[str, str]]] = None


def select_folder_windows(title: str, initial_dir: str = None) -> str:
    """使用现代 Windows 资源管理器风格的文件夹选择对话框"""
    import tempfile
    import os
    
    cs_code = '''
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
class FileOpenDialogCOM { }

[ComImport, Guid("42f85136-db7e-439c-85f1-e4075d135fc8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IFileOpenDialog {
    [PreserveSig] int Show(IntPtr hwndOwner);
    void SetFileTypes();
    void SetFileTypeIndex();
    void GetFileTypeIndex();
    void Advise();
    void Unadvise();
    void SetOptions(uint fos);
    void GetOptions();
    void SetDefaultFolder();
    void SetFolder(IShellItem psi);
    void GetFolder();
    void GetCurrentSelection();
    void SetFileName();
    void GetFileName();
    void SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
    void SetOkButtonLabel();
    void SetFileNameLabel();
    void GetResult(out IShellItem ppsi);
}

[ComImport, Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IShellItem {
    void BindToHandler();
    void GetParent();
    void GetDisplayName(uint sigdnName, out IntPtr ppszName);
    void GetAttributes();
    void Compare();
}

public class FolderPicker {
    [DllImport("user32.dll")]
    static extern IntPtr GetForegroundWindow();
    
    [DllImport("user32.dll")]
    static extern bool SetForegroundWindow(IntPtr hWnd);
    
    [DllImport("user32.dll")]
    static extern IntPtr GetDesktopWindow();

    public static string Show(string title) {
        IFileOpenDialog dialog = (IFileOpenDialog)new FileOpenDialogCOM();
        dialog.SetOptions(0x20 | 0x40);
        dialog.SetTitle(title);
        
        IntPtr hwnd = GetForegroundWindow();
        if (hwnd == IntPtr.Zero) {
            hwnd = GetDesktopWindow();
        }
        
        if (dialog.Show(hwnd) == 0) {
            IShellItem result;
            dialog.GetResult(out result);
            IntPtr pszPath;
            result.GetDisplayName(0x80058000, out pszPath);
            string path = Marshal.PtrToStringUni(pszPath);
            Marshal.FreeCoTaskMem(pszPath);
            return path;
        }
        return null;
    }
}
'''
    
    ps_script = f'''
$code = @"
{cs_code}
"@

try {{
    Add-Type -TypeDefinition $code -ErrorAction Stop
    $result = [FolderPicker]::Show("{title}")
    if ($result) {{
        Write-Output $result
    }}
}} catch {{
    Add-Type -AssemblyName System.Windows.Forms
    $fb = New-Object System.Windows.Forms.FolderBrowserDialog
    $fb.Description = "{title}"
    $fb.ShowNewFolderButton = $true
    if ($fb.ShowDialog() -eq 'OK') {{
        Write-Output $fb.SelectedPath
    }}
}}
'''
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False) as f:
        f.write(b'\xef\xbb\xbf')
        f.write(ps_script.encode('utf-8'))
        ps_file = f.name
    
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.stdout.strip()
    finally:
        os.unlink(ps_file)


def select_file_windows(title: str, initial_dir: str = None, file_filter: str = None) -> str:
    """使用 PowerShell 打开文件选择对话框"""
    import tempfile
    import os
    
    cs_code = '''
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
class FileOpenDialogCOM2 { }

[ComImport, Guid("42f85136-db7e-439c-85f1-e4075d135fc8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IFileOpenDialog2 {
    [PreserveSig] int Show(IntPtr hwndOwner);
    void SetFileTypes(uint cFileTypes, IntPtr rgFilterSpec);
    void SetFileTypeIndex(uint iFileType);
    void GetFileTypeIndex();
    void Advise();
    void Unadvise();
    void SetOptions(uint fos);
    void GetOptions();
    void SetDefaultFolder();
    void SetFolder(IShellItem2 psi);
    void GetFolder();
    void GetCurrentSelection();
    void SetFileName([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetFileName();
    void SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
    void SetOkButtonLabel();
    void SetFileNameLabel();
    void GetResult(out IShellItem2 ppsi);
}

[ComImport, Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IShellItem2 {
    void BindToHandler();
    void GetParent();
    void GetDisplayName(uint sigdnName, out IntPtr ppszName);
    void GetAttributes();
    void Compare();
}

public class FilePicker {
    [DllImport("user32.dll")]
    static extern IntPtr GetForegroundWindow();
    
    [DllImport("user32.dll")]
    static extern IntPtr GetDesktopWindow();

    public static string Show(string title) {
        IFileOpenDialog2 dialog = (IFileOpenDialog2)new FileOpenDialogCOM2();
        dialog.SetOptions(0x40);
        dialog.SetTitle(title);
        
        IntPtr hwnd = GetForegroundWindow();
        if (hwnd == IntPtr.Zero) {
            hwnd = GetDesktopWindow();
        }
        
        if (dialog.Show(hwnd) == 0) {
            IShellItem2 result;
            dialog.GetResult(out result);
            IntPtr pszPath;
            result.GetDisplayName(0x80058000, out pszPath);
            string path = Marshal.PtrToStringUni(pszPath);
            Marshal.FreeCoTaskMem(pszPath);
            return path;
        }
        return null;
    }
}
'''
    
    ps_script = f'''
$code = @"
{cs_code}
"@

try {{
    Add-Type -TypeDefinition $code -ErrorAction Stop
    $result = [FilePicker]::Show("{title}")
    if ($result) {{
        Write-Output $result
    }}
}} catch {{
    Add-Type -AssemblyName System.Windows.Forms
    $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $openFileDialog.Title = "{title}"
    {f'$openFileDialog.InitialDirectory = "{initial_dir}"' if initial_dir else ''}
    {f'$openFileDialog.Filter = "{file_filter}"' if file_filter else ''}
    if ($openFileDialog.ShowDialog() -eq 'OK') {{
        Write-Output $openFileDialog.FileName
    }}
}}
'''
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False) as f:
        f.write(b'\xef\xbb\xbf')
        f.write(ps_script.encode('utf-8'))
        ps_file = f.name
    
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.stdout.strip()
    finally:
        os.unlink(ps_file)


@router.post("/open-url")
async def open_url(request: OpenUrlRequest):
    """使用系统默认浏览器打开URL"""
    import webbrowser
    try:
        webbrowser.open(request.url)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/select-folder")
async def select_folder(request: FolderSelectRequest):
    """打开文件夹选择对话框"""
    try:
        folder_path = select_folder_windows(
            title=request.title or "选择文件夹",
            initial_dir=request.initialDir
        )
        
        if folder_path:
            return {"success": True, "path": folder_path}
        else:
            return {"success": False, "path": None, "message": "用户取消选择"}
    except Exception as e:
        return {"success": False, "path": None, "error": str(e)}


@router.post("/select-file")
async def select_file(request: FileSelectRequest):
    """打开文件选择对话框"""
    try:
        file_filter = None
        if request.fileTypes:
            filter_parts = []
            for desc, pattern in request.fileTypes:
                filter_parts.append(f"{desc}|{pattern}")
            file_filter = "|".join(filter_parts)
        
        file_path = select_file_windows(
            title=request.title or "选择文件",
            initial_dir=request.initialDir,
            file_filter=file_filter
        )
        
        if file_path:
            return {"success": True, "path": file_path}
        else:
            return {"success": False, "path": None, "message": "用户取消选择"}
    except Exception as e:
        return {"success": False, "path": None, "error": str(e)}
