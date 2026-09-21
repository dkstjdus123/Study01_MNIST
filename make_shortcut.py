# -*- coding: utf-8 -*-
"""
바탕 화면에 '손글씨 숫자 인식기' 바로가기를 만듭니다.

- 콘솔 창이 없는 pythonw.exe로 app.py를 직접 실행하므로 .py 파일 연결 설정과 무관하게 동작합니다.
- 전용 아이콘(app_icon.ico)을 만들어 바로가기에 지정합니다.
- app.py와 같은 앱 ID를 바로가기에 넣어, 작업 표시줄에 고정했을 때 실행 중인 창과 하나로 묶이게 합니다.

필요 패키지: pywin32 (python -m pip install pywin32)
"""

import os
import sys

import pythoncom
from PIL import Image, ImageDraw, ImageFont
from win32com.propsys import propsys, pscon
from win32com.shell import shell, shellcon

# app.py와 반드시 같은 값을 써야 하므로 직접 가져옵니다.
from app import 아이콘경로, 앱ID, 프로젝트폴더

바로가기이름 = "손글씨 숫자 인식기.lnk"


def 아이콘_만들기():
    """파란 둥근 사각형 위에 흰 숫자 '7'이 있는 아이콘을 여러 크기로 저장합니다."""
    크기 = 256
    그림 = Image.new("RGBA", (크기, 크기), (0, 0, 0, 0))
    붓 = ImageDraw.Draw(그림)
    붓.rounded_rectangle([8, 8, 크기 - 8, 크기 - 8], radius=48, fill=(26, 115, 232, 255))

    # 윈도우 기본 굵은 글꼴을 쓰고, 없으면 PIL 기본 글꼴을 씁니다.
    try:
        글꼴 = ImageFont.truetype("malgunbd.ttf", 200)
    except OSError:
        글꼴 = ImageFont.load_default(200)
    왼, 위, 오른, 아래 = 붓.textbbox((0, 0), "7", font=글꼴)
    위치 = ((크기 - (오른 - 왼)) / 2 - 왼, (크기 - (아래 - 위)) / 2 - 위)
    붓.text(위치, "7", font=글꼴, fill="white")

    그림.save(아이콘경로, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"아이콘 생성: {아이콘경로}")


def 바로가기_만들기():
    """pythonw.exe로 app.py를 실행하는 바탕 화면 바로가기를 만듭니다."""
    # 지금 실행 중인 파이썬(= torch가 설치된 파이썬)과 같은 폴더의 pythonw.exe를 사용합니다.
    pythonw경로 = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw경로):
        sys.exit(f"pythonw.exe를 찾을 수 없습니다: {pythonw경로}")
    앱경로 = os.path.join(프로젝트폴더, "app.py")

    바탕화면 = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0)
    저장경로 = os.path.join(바탕화면, 바로가기이름)

    링크 = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                     pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
    링크.SetPath(pythonw경로)
    링크.SetArguments(f'"{앱경로}"')
    링크.SetWorkingDirectory(프로젝트폴더)
    링크.SetIconLocation(아이콘경로, 0)
    링크.SetDescription("마우스로 쓴 손글씨 숫자를 인식합니다 (MNIST CNN)")

    # 작업 표시줄 고정 시 실행 중인 창과 묶이도록 앱 ID를 지정합니다.
    속성저장소 = 링크.QueryInterface(propsys.IID_IPropertyStore)
    속성저장소.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(앱ID, pythoncom.VT_LPWSTR))
    속성저장소.Commit()

    링크.QueryInterface(pythoncom.IID_IPersistFile).Save(저장경로, 0)
    print(f"바로가기 생성: {저장경로}")
    print(f"  실행 대상: {pythonw경로} \"{앱경로}\"")


if __name__ == "__main__":
    아이콘_만들기()
    바로가기_만들기()
