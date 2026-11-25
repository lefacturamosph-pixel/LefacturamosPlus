import os
import zipfile
import subprocess
import shutil
import re

def bundle():
    with open('www/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    with open('www/app.js', 'r', encoding='utf-8') as f:
        js = f.read()

    pattern = r'<script src="/?app\.js[^"]*"></script>'
    m = re.search(pattern, html)
    if not m:
        print('Target <script src="app.js"></script> not found!')
        return

    bundle_content = html[:m.start()] + f'<script>\n{js}\n</script>' + html[m.end():]
    paths = [
        'lefacturamos_aistudio.html',
        'www/lefacturamos_aistudio.html',
        'android/app/src/main/assets/public/lefacturamos_aistudio.html'
    ]
    for p in paths:
        if os.path.exists(os.path.dirname(p) or '.'):
            with open(p, 'w', encoding='utf-8') as out:
                out.write(bundle_content)
            print(f'Successfully bundled {p} ({len(bundle_content)} bytes)')

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
        idx_bytes = html.encode('utf-8')
        js_bytes = js.encode('utf-8')
        bundle_bytes = bundle_content.encode('utf-8')

        with zipfile.ZipFile(apk_path, 'r') as zin, zipfile.ZipFile(temp_apk, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
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
                elif item.filename == 'assets/public/assets/xlsx.full.min.js' and os.path.exists('www/assets/xlsx.full.min.js'):
                    with open('www/assets/xlsx.full.min.js', 'rb') as xf:
                        zout.writestr(item, xf.read())
                elif item.filename == 'assets/public/assets/html5-qrcode.min.js' and os.path.exists('www/assets/html5-qrcode.min.js'):
                    with open('www/assets/html5-qrcode.min.js', 'rb') as qrf:
                        zout.writestr(item, qrf.read())
                else:
                    zout.writestr(item, zin.read(item.filename))

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
                for mirror in [
                    'LEFACTURAMOS.apk',
                    'www/Lefacturamos.apk',
                    'android/app/build/outputs/apk/debug/app-debug.apk',
                    'android/app/src/main/assets/public/Lefacturamos.apk'
                ]:
                    if os.path.exists(os.path.dirname(mirror)):
                        shutil.copyfile(apk_path, mirror)
                        print(f'Mirrored signed APK to {mirror}')
            else:
                print('apksigner error:', res.stderr)

if __name__ == '__main__':
    bundle()
