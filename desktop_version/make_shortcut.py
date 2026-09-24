# 작성: 2026-09-24 23:33
"""바탕 화면에 '손글씨 숫자 인식기' 바로가기를 만듭니다 (Windows 전용).

- 콘솔 창이 없는 pythonw.exe로 app.py를 실행합니다 (검은 창 없음).
- app_icon.ico를 만들어 바로가기와 창 아이콘으로 씁니다.
- app.py와 같은 앱ID를 넣어, 작업 표시줄에 고정하면 실행 중인 창과 하나로 묶입니다.
필요 패키지: python -m pip install pywin32 pillow
실행: python make_shortcut.py  (폴더를 옮겼으면 다시 실행)
"""

import os
import sys

from PIL import Image, ImageDraw

from app import 아이콘경로, 앱ID, 프로젝트폴더

바로가기이름 = "손글씨 숫자 인식기.lnk"


def 아이콘_만들기():
    """어두운 둥근 사각형에 흰 숫자 7을 그린 아이콘(16~256px)을 app_icon.ico로 저장합니다."""
    그림 = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    붓 = ImageDraw.Draw(그림)
    붓.rounded_rectangle((8, 8, 248, 248), radius=44, fill=(25, 25, 25, 255))
    붓.line([(72, 72), (184, 72), (112, 200)], fill=(255, 255, 255, 255), width=30, joint="curve")
    그림.save(아이콘경로, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])


def 바로가기_만들기():
    import pythoncom
    from win32com.propsys import propsys, pscon
    from win32com.shell import shell, shellcon

    바탕화면 = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0)
    바로가기경로 = os.path.join(바탕화면, 바로가기이름)
    pythonw경로 = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")

    링크 = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER,
                                      shell.IID_IShellLink)
    링크.SetPath(pythonw경로)
    링크.SetArguments(f'"{os.path.join(프로젝트폴더, "app.py")}"')
    링크.SetWorkingDirectory(프로젝트폴더)
    링크.SetIconLocation(아이콘경로, 0)
    링크.SetDescription("마우스로 그린 숫자를 인식합니다")
    속성 = 링크.QueryInterface(propsys.IID_IPropertyStore)
    속성.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(앱ID, pythoncom.VT_LPWSTR))
    속성.Commit()
    링크.QueryInterface(pythoncom.IID_IPersistFile).Save(바로가기경로, 0)
    return 바로가기경로


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("바로가기는 Windows에서만 만들 수 있습니다.")
    아이콘_만들기()
    print("바로가기를 만들었습니다:", 바로가기_만들기())
