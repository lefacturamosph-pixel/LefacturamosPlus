Add-Type -AssemblyName System.Drawing
$imgPath = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\.user_uploaded\media_1792190591434_7fab248c.png'
$img = [System.Drawing.Image]::FromFile($imgPath)
$w = $img.Width
$h = $img.Height
Write-Host "Image dimensions: $w x $h"

$scratchDir = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch'
if (!(Test-Path $scratchDir)) { New-Item -ItemType Directory -Path $scratchDir }

function Save-Crop($x, $y, $cw, $ch, $filename) {
    $rect = New-Object System.Drawing.Rectangle $x, $y, $cw, $ch
    $bmp = New-Object System.Drawing.Bitmap $rect.Width, $rect.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $rect.Width, $rect.Height), $rect, [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    $outPath = Join-Path $scratchDir $filename
    $bmp.Save($outPath)
    $bmp.Dispose()
    Write-Host "Saved $filename"
}

# Image is 1024 x 576. The main content is on the right of sidebar (x from ~140 to 1010).
# 1. Top white alert/banner: y ~ 135 to 175
Save-Crop 220 135 700 45 'crop_top_banner.png'

# 2. Main Central Drive card: y ~ 170 to 300
Save-Crop 220 170 700 130 'crop_central_card.png'

# 3. Folders section header & buttons: y ~ 300 to 350
Save-Crop 220 305 700 45 'crop_folders_header.png'

# 4. Folder cards 1, 2, 3: y ~ 350 to 500
Save-Crop 230 350 225 150 'crop_folder1.png'
Save-Crop 460 350 225 150 'crop_folder2.png'
Save-Crop 690 350 225 150 'crop_folder3.png'

# 5. Bottom card (Manual de Convivencia): y ~ 500 to 565
Save-Crop 220 500 700 65 'crop_bottom_card.png'

$img.Dispose()
