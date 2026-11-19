Add-Type -AssemblyName System.Drawing
$imgPath = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\.user_uploaded\media_1792187092971_3ac1afcd.png'
$img = [System.Drawing.Image]::FromFile($imgPath)
$w = $img.Width
$h = $img.Height

# Crop 3: Bottom portion below option 1 (y: 470 to 576)
$rect3 = New-Object System.Drawing.Rectangle 220, 470, 720, 95
$bmp3 = New-Object System.Drawing.Bitmap $rect3.Width, $rect3.Height
$g3 = [System.Drawing.Graphics]::FromImage($bmp3)
$g3.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $rect3.Width, $rect3.Height), $rect3, [System.Drawing.GraphicsUnit]::Pixel)
$bmp3.Save('C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch\crop3.png')

$img.Dispose()
Write-Host "Crop 3 saved"
