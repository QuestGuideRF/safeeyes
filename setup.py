import os ,sys ,site
import subprocess
import setuptools
requires =[
'babel',
'psutil',
'croniter',
'PyGObject',
'python-xlib'
]
_ROOT =os .path .abspath (os .path .dirname (__file__ ))
with open (os .path .join (_ROOT ,'README.md'))as f :
    long_description =f .read ()
def __compile_po_files ():
    localedir ='safeeyes/config/locale'
    po_dirs =[localedir +'/'+l +'/LC_MESSAGES/'
    for l in next (os .walk (localedir ))[1 ]]
    for po_dir in po_dirs :
        po_files =[f
        for f in next (os .walk (po_dir ))[2 ]
        if os .path .splitext (f )[1 ]=='.po']
        for po_file in po_files :
            filename ,_ =os .path .splitext (po_file )
            mo_file =filename +'.mo'
            msgfmt_cmd ='мсгфмт {} -о {}'.format (
            po_dir +po_file ,po_dir +mo_file )
            subprocess .call (msgfmt_cmd ,shell =True )
def __data_files ():
    root_dir =sys .prefix
    return [(os .path .join (root_dir ,"share/applications"),["safeeyes/platform/io.github.slgobinath.SafeEyes.desktop"]),
    (os .path .join (root_dir ,"share/icons/hicolor/24x24/status"),["safeeyes/platform/icons/hicolor/24x24/status/io.github.slgobinath.SafeEyes-disabled.png","safeeyes/platform/icons/hicolor/24x24/status/io.github.slgobinath.SafeEyes-enabled.png","safeeyes/platform/icons/hicolor/24x24/status/io.github.slgobinath.SafeEyes-timer.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/24x24/apps"),["safeeyes/platform/icons/hicolor/24x24/apps/io.github.slgobinath.SafeEyes.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/16x16/status"),["safeeyes/platform/icons/hicolor/16x16/status/io.github.slgobinath.SafeEyes-disabled.png","safeeyes/platform/icons/hicolor/16x16/status/io.github.slgobinath.SafeEyes-enabled.png","safeeyes/platform/icons/hicolor/16x16/status/io.github.slgobinath.SafeEyes-timer.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/16x16/apps"),["safeeyes/platform/icons/hicolor/16x16/apps/io.github.slgobinath.SafeEyes.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/32x32/status"),["safeeyes/platform/icons/hicolor/32x32/status/io.github.slgobinath.SafeEyes-disabled.png","safeeyes/platform/icons/hicolor/32x32/status/io.github.slgobinath.SafeEyes-enabled.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/32x32/apps"),["safeeyes/platform/icons/hicolor/32x32/apps/io.github.slgobinath.SafeEyes.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/64x64/apps"),["safeeyes/platform/icons/hicolor/64x64/apps/io.github.slgobinath.SafeEyes.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/128x128/apps"),["safeeyes/platform/icons/hicolor/128x128/apps/io.github.slgobinath.SafeEyes.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/48x48/status"),["safeeyes/platform/icons/hicolor/48x48/status/io.github.slgobinath.SafeEyes-disabled.png","safeeyes/platform/icons/hicolor/48x48/status/io.github.slgobinath.SafeEyes-enabled.png"]),
    (os .path .join (root_dir ,"share/icons/hicolor/48x48/apps"),["safeeyes/platform/icons/hicolor/48x48/apps/io.github.slgobinath.SafeEyes.png"]),]
def __package_files (directory ):
    paths =[]
    for (path ,_ ,filenames )in os .walk (directory ):
        for filename in filenames :
            paths .append (os .path .join ('..',path ,filename ))
    return paths
def __package_data ():
    __compile_po_files ()
    data =['счастлив/*.счастлив','ресурс/*']
    data .extend (__package_files ('safeeyes/config'))
    data .extend (__package_files ('safeeyes/plugins'))
    data .extend (__package_files ('safeeyes/platform'))
    return data
setuptools .setup (
name ="safeeyes",
version ="2.1.6",
description ="Защитите свои глаза от перенапряжения глаз с помощью этого напоминания о непрерывных перерывах.",
long_description =long_description ,
long_description_content_type ="text/markdown",
author ="Гобинат Логанатан",
author_email ="slgobinath@gmail.com",
url ="https://github.com/slgobinath/SafeEyes",
download_url ="https://github.com/slgobinath/SafeEyes/archive/v2.1.6.tar.gz",
packages =setuptools .find_packages (),
package_data ={'safeeyes':__package_data ()},
data_files =__data_files (),
install_requires =requires ,
entry_points ={'console_scripts':['Safeeyes = Safeeyes.__main__:main']},
keywords ='Утилита Linux для здоровья, напряжения глаз, безопасных глаз',
classifiers =[
"Операционная система :: POSIX :: Linux",
"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
"Статус разработки :: 5 - Производство/Стабильный",
"Окружающая среда :: Приложения X11 :: GTK",
"Целевая аудитория :: Конечные пользователи/рабочие столы",
"Тема :: Утилиты"]+[('Язык программирования :: Python :: %s'%x )for x in '3 3.5 3.6 3.7 3.8 3.9'.split ()]
)