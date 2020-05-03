# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['nmlc'],
             pathex=['.'],
             binaries=[('./nml_lz77.*.pyd', '.')],
             datas=[],
             hiddenimports=[
                'nml.generated.lextab',
                'nml.generated.parsetab',
                'pkg_resources.py2_warn' # needed for setuptools >= 45 and pyinstaller <= 3.6
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='nmlc',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
