Add-Type -AssemblyName System.Drawing
$imgPath = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\.user_uploaded\media_1792240690719_9141a5e4.png'
$img = [System.Drawing.Image]::FromFile($imgPath)

$scratchDir = 'C:\Users\CARLOS\.gemini\antigravity\brain\de963477-d937-4673-b142-7982134fb1b8\scratch'

function Save-Zoom-Crop($x, $y, $cw, $ch, $filename) {
    $rect = New-Object System.Drawing.Rectangle $x, $y, $cw, $ch
    $targetW = $cw * 2
    $targetH = $ch * 2
    $bmp = New-Object System.Drawing.Bitmap $targetW, $targetH
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $targetW, $targetH), $rect, [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    $outPath = Join-Path $scratchDir $filename
    $bmp.Save($outPath)
    $bmp.Dispose()
    Write-Host "Saved $filename"
}

Save-Zoom-Crop 370 185 255 130 'crop_zoom_top.png'
Save-Zoom-Crop 370 295 255 165 'crop_zoom_bottom.png'

$img.Dispose()
