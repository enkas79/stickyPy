; Script NSIS per l'installer Windows di StickyPy.
; Costruito dalla CI a partire dall'output onedir di PyInstaller in dist\StickyPy\
; (una vera cartella applicazione, non un eseguibile onefile autoestraente).
; La versione arriva da riga di comando: makensis /DVERSION=1.2.3 installer.nsi

!ifndef VERSION
  !define VERSION "0.0.0"
!endif

Name "StickyPy"
; I percorsi relativi in questo script (OutFile, File) si risolvono rispetto
; alla cartella dello script stesso (packaging/windows), non alla cwd di
; makensis. Lasciarlo senza percorso assoluto: l'installer finisce accanto
; a questo script, dove il workflow se lo aspetta per upload-artifact.
OutFile "StickyPy-Setup-${VERSION}.exe"
InstallDir "$PROGRAMFILES64\StickyPy"
RequestExecutionLevel admin

Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "..\..\dist\StickyPy\*.*"
    CreateDirectory "$SMPROGRAMS\StickyPy"
    CreateShortcut "$SMPROGRAMS\StickyPy\StickyPy.lnk" "$INSTDIR\StickyPy.exe"
    CreateShortcut "$DESKTOP\StickyPy.lnk" "$INSTDIR\StickyPy.exe"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\StickyPy\StickyPy.lnk"
    RMDir "$SMPROGRAMS\StickyPy"
    Delete "$DESKTOP\StickyPy.lnk"
SectionEnd
