Add-Type -AssemblyName System.Drawing
$imgPath = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\.user_uploaded\media_1792187988267_c211f822.png'
$img = [System.Drawing.Image]::FromFile($imgPath)
$w = $img.Width
$h = $img.Height
Write-Host "Size: $w x $h"

# Crop 1: Header + Row 1 (y: 120 to 330)
$rect1 = New-Object System.Drawing.Rectangle 220, 120, 750, 210
$bmp1 = New-Object System.Drawing.Bitmap $rect1.Width, $rect1.Height
$g1 = [System.Drawing.Graphics]::FromImage($bmp1)
$g1.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $rect1.Width, $rect1.Height), $rect1, [System.Drawing.GraphicsUnit]::Pixel)
$bmp1.Save('C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch\zonas_crop1.png')

# Crop 2: Row 2 (y: 300 to 450)
$rect2 = New-Object System.Drawing.Rectangle 220, 300, 750, 150
$bmp2 = New-Object System.Drawing.Bitmap $rect2.Width, $rect2.Height
$g2 = [System.Drawing.Graphics]::FromImage($bmp2)
$g2.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $rect2.Width, $rect2.Height), $rect2, [System.Drawing.GraphicsUnit]::Pixel)
$bmp2.Save('C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch\zonas_crop2.png')

# Crop 3: Row 3 (y: 430 to 576)
$rect3 = New-Object System.Drawing.Rectangle 220, 430, 750, 140
$bmp3 = New-Object System.Drawing.Bitmap $rect3.Width, $rect3.Height
$g3 = [System.Drawing.Graphics]::FromImage($bmp3)
$g3.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $rect3.Width, $rect3.Height), $rect3, [System.Drawing.GraphicsUnit]::Pixel)
$bmp3.Save('C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch\zonas_crop3.png')

$img.Dispose()
Write-Host "Zonas crops saved"
