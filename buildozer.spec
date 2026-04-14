[app]

title = Eye Control System
package.name = eyecontrol
package.domain = org.nurse.step7
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,wav,yaml,yml,dat,ttf,otf
version = 0.1.0

requirements = python3,kivy==2.3.0,numpy,opencv,opencv_extras,plyer,android

orientation = landscape
fullscreen = 1

android.permissions = INTERNET,CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
