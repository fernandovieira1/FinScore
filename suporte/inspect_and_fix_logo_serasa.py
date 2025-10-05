from PIL import Image
from collections import Counter
import os

orig = r"c:\Users\ferna\OneDrive\Desktop OneDrive\FinScore\app_front\assets\logo_serasa.png"
out = r"c:\Users\ferna\OneDrive\Desktop OneDrive\FinScore\app_front\assets\logo_serasa_fixed.png"

print('Orig path:', out)
if not os.path.exists(orig):
    print('ERROR: original file not found')
    raise SystemExit(1)

im = Image.open(orig)
print('mode:', im.mode, 'size:', im.size)

# Check alpha
has_alpha = 'A' in im.getbands()
print('has_alpha:', has_alpha)
if has_alpha:
    a = im.split()[-1]
    arr = a.getdata()
    total = im.size[0]*im.size[1]
    transparent_count = sum(1 for v in arr if v < 255)
    print('transparent pixels <255:', transparent_count, 'of', total)

# Sample border colors to detect checkerboard (default sample_border=6)
w,h = im.size
pixels = im.convert('RGB').load()
sample_border = 6
samples = []
for x in range(0, w):
    for y in range(sample_border):
        samples.append(pixels[x,y])
    for y in range(max(0,h-sample_border), h):
        samples.append(pixels[x,y])
for y in range(0, h):
    for x in range(sample_border):
        samples.append(pixels[x,y])
    for x in range(max(0,w-sample_border), w):
        samples.append(pixels[x,y])

count = Counter(samples)
print('\nMost common border colors (top 8):')
for c, n in count.most_common(8):
    print(c, n)

# Try detect candidate checker colors: take top 2 if they occupy a large fraction
most = [c for c,_ in count.most_common(6)]
candidate_bg = most[:2]
print('\nCandidate checker colors:', candidate_bg)

# Quick heuristic: if those colors appear frequently across the image and in a checker pattern, remove them
rgb_im = im.convert('RGB')
arr = rgb_im.load()

# Count frequency across whole image
total_pixels = w*h
freq = Counter()
for y in range(h):
    for x in range(w):
        freq[arr[x,y]] += 1
print('\nTop colors in whole image (top 6):')
for c,n in freq.most_common(6):
    print(c,n)

# If candidate colors are present, produce a replacement by mapping exact matches to background
bg = (253,250,251)
mapped = 0
out_img = Image.new('RGB', (w,h), bg)
out_px = out_img.load()
for y in range(h):
    for x in range(w):
        p = arr[x,y]
        if p in candidate_bg:
            out_px[x,y] = bg
            mapped += 1
        else:
            out_px[x,y] = p

print('\nMapped pixels replaced:', mapped, 'of', total_pixels)
# Save output
out_img.save(out)
print('Saved fixed image to', out)

# Show simple advice
if mapped < total_pixels * 0.001:
    print('\nNote: only a few pixels matched candidate colors. If the checkerboard uses anti-aliased tones, increase thresholding or run a distance-based replace.')
else:
    print('\nIf the fixed image looks good, use this file in the app (replace original or reference fixed file).')
