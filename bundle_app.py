import os
import zipfile
import subprocess
import shutil

with open('www/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('www/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re

pattern = r'<script src="/?app\.js[^"]*"></script>'
m = re.search(pattern, html)
if m:
    bundle = html[:m.start()] + f'<script>\n{js}\n</script>' + html[m.end():]
    paths = [
        'lefacturamos_aistudio.html',
        'www/lefacturamos_aistudio.html',
        'android/app/src/main/assets/public/lefacturamos_aistudio.html'
    ]
    for p in paths:
        if os.path.exists(os.path.dirname(p) or '.'):
            with open(p, 'w', encoding='utf-8') as out:
                out.write(bundle)
            print(f'Successfully bundled {p} ({len(bundle)} bytes)')

    # Also copy index.html and app.js to android assets
    android_public = 'android/app/src/main/assets/public'
    if os.path.exists(android_public):
        with open(os.path.join(android_public, 'index.html'), 'w', encoding='utf-8') as out:
            out.write(html)
        with open(os.path.join(android_public, 'app.js'), 'w', encoding='utf-8') as out:
            out.write(js)
        print(f'Successfully copied index.html and app.js to {android_public}')

    # Inject, align, and sign APK
    apk_path = 'LEFACTURAMOS_Android_v4.apk'
    temp_apk = 'LEFACTURAMOS_temp.apk'
    aligned_apk = 'LEFACTURAMOS_aligned.apk'

    if os.path.exists(apk_path):
        with open('www/index.html', 'rb') as f:
            idx_bytes = f.read()
        with open('www/app.js', 'rb') as f:
            js_bytes = f.read()
        bundle_bytes = bundle.encode('utf-8')

        with zipfile.ZipFile(apk_path, 'r') as zin, zipfile.ZipFile(temp_apk, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            has_xlsx = False
            has_qr = False
            for item in zin.infolist():
                fname_upper = item.filename.upper()
                if fname_upper.startswith('META-INF/') and (
                    fname_upper.endswith('.SF') or 
                    fname_upper.endswith('.RSA') or 
                    fname_upper.endswith('.DSA') or 
                    fname_upper.endswith('.MF')
                ):
                    continue
                if item.filename == 'assets/public/index.html':
                    zout.writestr(item, idx_bytes)
                elif item.filename == 'assets/public/app.js':
                    zout.writestr(item, js_bytes)
                elif item.filename == 'assets/public/lefacturamos_aistudio.html':
                    zout.writestr(item, bundle_bytes)
                elif item.filename == 'assets/public/assets/xlsx.full.min.js':
                    has_xlsx = True
                    if os.path.exists('www/assets/xlsx.full.min.js'):
                        with open('www/assets/xlsx.full.min.js', 'rb') as xf:
                            zout.writestr(item, xf.read())
                    else:
                        zout.writestr(item, zin.read(item.filename))
                elif item.filename == 'assets/public/assets/html5-qrcode.min.js':
                    has_qr = True
                    if os.path.exists('www/assets/html5-qrcode.min.js'):
                        with open('www/assets/html5-qrcode.min.js', 'rb') as qrf:
                            zout.writestr(item, qrf.read())
                    else:
                        zout.writestr(item, zin.read(item.filename))
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not has_xlsx and os.path.exists('www/assets/xlsx.full.min.js'):
                with open('www/assets/xlsx.full.min.js', 'rb') as xf:
                    zout.writestr('assets/public/assets/xlsx.full.min.js', xf.read())
            if not has_qr and os.path.exists('www/assets/html5-qrcode.min.js'):
                with open('www/assets/html5-qrcode.min.js', 'rb') as qrf:
                    zout.writestr('assets/public/assets/html5-qrcode.min.js', qrf.read())

        zipalign = r'C:\Users\CARLOS\AppData\Local\Android\Sdk\build-tools\34.0.0\zipalign.exe'
        apksigner = r'C:\Users\CARLOS\AppData\Local\Android\Sdk\build-tools\34.0.0\apksigner.bat'
        keystore = os.path.expanduser('~/.android/debug.keystore')

        # 1. zipalign -p -f 4
        if os.path.exists(zipalign):
            if os.path.exists(aligned_apk):
                os.remove(aligned_apk)
            zres = subprocess.run([zipalign, '-p', '-f', '4', temp_apk, aligned_apk], capture_output=True, text=True)
            if zres.returncode == 0:
                print('APK successfully zipalign-ed (4-byte page aligned).')
                if os.path.exists(temp_apk):
                    os.remove(temp_apk)
            else:
                print('zipalign warning:', zres.stderr)
                os.replace(temp_apk, aligned_apk)
        else:
            os.replace(temp_apk, aligned_apk)

        # 2. apksigner sign (v1 + v2 + v3 schemes)
        if os.path.exists(apksigner) and os.path.exists(keystore):
            env = os.environ.copy()
            env['JAVA_HOME'] = r'C:\Program Files\Android\Android Studio\jbr'
            env['PATH'] = os.path.join(env['JAVA_HOME'], 'bin') + ';' + env.get('PATH', '')
            env['_JAVA_OPTIONS'] = '-Xmx256m'
            res = subprocess.run([
                apksigner, 'sign',
                '--ks', keystore,
                '--ks-pass', 'pass:android',
                '--key-pass', 'pass:android',
                '--min-sdk-version', '21',
                '--v1-signing-enabled', 'true',
                '--v2-signing-enabled', 'true',
                '--v3-signing-enabled', 'true',
                aligned_apk
            ], capture_output=True, text=True, env=env)
            if res.returncode == 0:
                os.replace(aligned_apk, apk_path)
                print('LEFACTURAMOS_Android_v4.apk successfully updated, aligned, and signed (v1, v2, v3)!')
                debug_apk = 'android/app/build/outputs/apk/debug/app-debug.apk'
                if os.path.exists(os.path.dirname(debug_apk)):
                    shutil.copyfile(apk_path, debug_apk)
                    print(f'Successfully mirrored signed APK to {debug_apk}')
            else:
                print('apksigner error:', res.stderr)
else:
    print('Target <script src="app.js"></script> not found!')
