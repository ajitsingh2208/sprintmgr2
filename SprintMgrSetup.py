from distutils.core import setup
import os
import shutil
import zipfile

distDir = 'dist'

googleDrive = r"c:\GoogleDrive\Downloads\Windows\CrossMgr"
if not os.path.exists(googleDrive):
	googleDrive = r"C:\Users\Edward Sitarski\Google Drive\Downloads\Windows\CrossMgr"

# Cleanup existing dll, pyd and exe files.  The old ones may not be needed, so it is best to clean these up.
for f in os.listdir(distDir):
	if f.endswith('.dll') or f.endswith('.pyd') or f.endswith('.exe'):
		fname = os.path.join(distDir, f)
		print 'deleting:', fname
		os.remove( fname )
		
from Version import AppVerName
def make_inno_version():
	setup = {
		'AppName':				AppVerName.split()[0],
		'AppPublisher':			"Edward Sitarski",
		'AppContact':			"Edward Sitarski",
		'AppCopyright':			"Copyright (C) 2004-{} Edward Sitarski".format(datetime.date.today().year),
		'AppVerName':			AppVerName,
		'AppPublisherURL':		"http://www.sites.google.com/site/crossmgrsoftware/",
		'AppUpdatesURL':		"http://www.sites.google.com/site/crossmgrsoftware/downloads/",
		'VersionInfoVersion':	AppVerName.split()[1],
	}
	with open('inno_setup.txt', 'w') as f:
		for k, v in setup.iteritems():
			f.write( '{}={}\n'.format(k,v) )
make_inno_version()

cmd = '"' + inno + '" ' + 'CrossMgr.iss'
print cmd
subprocess.call( cmd, shell=True )

# Copy additional dlls to distribution folder.
wxHome = r'C:\Python27\Lib\site-packages\wx-2.8-msw-ansi\wx'
try:
	shutil.copy( os.path.join(wxHome, 'MSVCP71.dll'), distDir )
except:
	pass
try:
	shutil.copy( os.path.join(wxHome, 'gdiplus.dll'), distDir )
except:
	pass

# Add images to the distribution folder.

def copyDir( d ):
	destD = os.path.join(distDir, d)
	if os.path.exists( destD ):
		shutil.rmtree( destD )
	os.mkdir( destD )
	for i in os.listdir( d ):
		if i[-3:] != '.db':	# Ignore .db files.
			shutil.copy( os.path.join(d, i), os.path.join(destD,i) )
			
copyDir( 'images' )
#copyDir( 'data' )
#copyDir( 'html' )

# Create the installer
inno = r'\Program Files (x86)\Inno Setup 5\ISCC.exe'
# Find the drive inno is installed on.
for drive in ['C', 'D']:
	innoTest = drive + ':' + inno
	if os.path.exists( innoTest ):
		inno = innoTest
		break

cmd = '"' + inno + '" ' + 'SprintMgr.iss'
print cmd
os.system( cmd )

# Create versioned executable.
from Version import AppVerName
vNum = AppVerName.split()[1]
vNum = vNum.replace( '.', '_' )
newExeName = 'SprintMgr_Setup_v' + vNum + '.exe'

try:
	os.remove( 'install\\' + newExeName )
except:
	pass
	
shutil.copy( 'install\\SprintMgr_Setup.exe', 'install\\' + newExeName )
print 'executable copied to: ' + newExeName

# Create comprssed executable.
os.chdir( 'install' )
newExeName = os.path.basename( newExeName )
newZipName = newExeName.replace( '.exe', '.zip' )

try:
	os.remove( newZipName )
except:
	pass

z = zipfile.ZipFile(newZipName, "w")
z.write( newExeName )
z.close()
print 'executable compressed.'

shutil.copy( newExeName, r"c:\GoogleDrive\Downloads\Windows\SprintMgr"  )

os.chdir( '..' )
shutil.copy( 'SprintMgrTutorial.pdf', r"c:\GoogleDrive\Downloads\Windows\SprintMgr"  )

