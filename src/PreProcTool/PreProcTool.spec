# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\main.py'],
             pathex=['src'],
             binaries=[],
             datas=[( 'src\\config', 'config' ), ( '..\\WebVisTool\\build\\dist', 'webbase' ), ('src\\proj', 'proj')],
             hiddenimports=['scipy.special._ufuncs_cxx'],
             hookspath=[],
             runtime_hooks=['src\\hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
	  name='PreProcTool',
	  debug=False,
	  strip=False,
	  upx=True,
	  console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='PreProcTool')
          
          
          
          
          
