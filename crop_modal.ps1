Add-Type -AssemblyName System.Drawing
$imgPath = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\.user_uploaded\media_1792189226161_339301f1.png'
$img = [System.Drawing.Image]::FromFile($imgPath)
$w = $img.Width
$h = $img.Height
Write-Host "Size: $w x $h"

# Crop the modal in center: x from ~350 to ~670, y from ~150 to ~500 (normalized to 1024x576)
$rect = New-Object System.Drawing.Rectangle 360, 150, 310, 340
$bmp = New-Object System.Drawing.Bitmap $rect.Width, $rect.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $rect.Width, $rect.Height), $rect, [System.Drawing.GraphicsUnit]::Pixel)
$bmp.Save('C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch\modal_crop.png')

$img.Dispose()
Write-Host "Modal crop saved"
