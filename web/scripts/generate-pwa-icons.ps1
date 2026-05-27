Set-StrictMode -Version Latest

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$iconsDir = Join-Path $root "public\icons"
$appDir = Join-Path $root "src\app"

New-Item -ItemType Directory -Force -Path $iconsDir | Out-Null

function New-AutoTacheBitmap {
    param(
        [Parameter(Mandatory = $true)][int]$Size,
        [Parameter(Mandatory = $true)][double]$Scale
    )

    $bitmap = New-Object System.Drawing.Bitmap $Size, $Size
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $graphics.Clear([System.Drawing.Color]::FromArgb(15, 23, 42))

    $center = $Size / 2.0
    $s = $Size * $Scale / 512.0
    $offset = $center - (256.0 * $s)

    function X([double]$value) { return [single]($offset + ($value * $s)) }
    function W([double]$value) { return [single]($value * $s) }

    $teal = [System.Drawing.Color]::FromArgb(20, 184, 166)
    $slate100 = [System.Drawing.Color]::FromArgb(226, 232, 240)
    $white = [System.Drawing.Color]::FromArgb(248, 250, 252)

    $linePen = New-Object System.Drawing.Pen $slate100, (W 26)
    $linePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $linePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    $tealPen = New-Object System.Drawing.Pen $teal, (W 28)
    $tealPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $tealPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $tealPen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round

    $checkPen = New-Object System.Drawing.Pen $teal, (W 34)
    $checkPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $checkPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $checkPen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round

    $graphics.DrawLine($linePen, (X 122), (X 178), (X 234), (X 178))
    $graphics.DrawLine($linePen, (X 122), (X 256), (X 278), (X 256))
    $graphics.DrawLine($linePen, (X 122), (X 334), (X 238), (X 334))

    $graphics.DrawEllipse($tealPen, (X 318), (X 90), (W 116), (W 116))
    $graphics.DrawLine($tealPen, (X 416), (X 188), (X 470), (X 242))
    $graphics.DrawLines($checkPen, @(
        (New-Object System.Drawing.PointF (X 302), (X 321)),
        (New-Object System.Drawing.PointF (X 340), (X 359)),
        (New-Object System.Drawing.PointF (X 422), (X 263))
    ))

    $fontSize = [single](92 * $s)
    $font = New-Object System.Drawing.Font "Arial", $fontSize, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
    $brush = New-Object System.Drawing.SolidBrush $white
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Near
    $format.LineAlignment = [System.Drawing.StringAlignment]::Near
    $graphics.DrawString("AT", $font, $brush, (X 110), (X 354), $format)

    $format.Dispose()
    $brush.Dispose()
    $font.Dispose()
    $checkPen.Dispose()
    $tealPen.Dispose()
    $linePen.Dispose()
    $graphics.Dispose()

    return $bitmap
}

function Save-Png {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][int]$Size,
        [Parameter(Mandatory = $true)][double]$Scale
    )

    $bitmap = New-AutoTacheBitmap -Size $Size -Scale $Scale
    try {
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $bitmap.Dispose()
    }
}

function Save-IcoFromPng {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$PngPath
    )

    $pngBytes = [System.IO.File]::ReadAllBytes($PngPath)
    $stream = New-Object System.IO.MemoryStream
    $writer = New-Object System.IO.BinaryWriter $stream

    $writer.Write([UInt16]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]1)
    $writer.Write([byte]32)
    $writer.Write([byte]32)
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([UInt16]1)
    $writer.Write([UInt16]32)
    $writer.Write([UInt32]$pngBytes.Length)
    $writer.Write([UInt32]22)
    $writer.Write($pngBytes)
    $writer.Flush()

    [System.IO.File]::WriteAllBytes($Path, $stream.ToArray())

    $writer.Dispose()
    $stream.Dispose()
}

$faviconPng = Join-Path $iconsDir "favicon-32.png"

Save-Png -Path (Join-Path $iconsDir "icon-192.png") -Size 192 -Scale 1.0
Save-Png -Path (Join-Path $iconsDir "icon-512.png") -Size 512 -Scale 1.0
Save-Png -Path (Join-Path $iconsDir "icon-maskable-512.png") -Size 512 -Scale 0.78
Save-Png -Path (Join-Path $appDir "apple-icon.png") -Size 180 -Scale 0.92
Save-Png -Path $faviconPng -Size 32 -Scale 1.0
Save-IcoFromPng -Path (Join-Path $appDir "favicon.ico") -PngPath $faviconPng
Remove-Item -LiteralPath $faviconPng -Force
