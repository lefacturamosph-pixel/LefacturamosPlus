Add-Type -AssemblyName System.Drawing
$imgPath = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\.user_uploaded\media_1792240690719_9141a5e4.png'
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

# Image is 1024 x 576.
# Modal is centered roughly from x: 375 to 640 (width ~265), y: 180 to 450 (height ~270)
Save-Crop 360 180 270 280 'crop_modal_copropiedad.png'
Save-Crop 360 180 270 140 'crop_modal_top.png'
Save-Crop 360 300 270 160 'crop_modal_bottom.png'

$img.Dispose()
