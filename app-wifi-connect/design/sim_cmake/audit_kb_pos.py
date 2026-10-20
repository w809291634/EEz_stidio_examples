from PIL import Image
im = Image.open('shot_fake.bmp').convert('L')
box = im.crop((0, 150, 480, 240))
w, h = box.size
px = box.load()
cols = [x for x in range(w) if any(px[x, y] > 90 for y in range(h))]
rows = [y for y in range(h) if any(px[x, y] > 90 for y in range(h))]
print('键盘亮区 x: %d..%d (宽 %d, 中心 %d)' % (cols[0], cols[-1], cols[-1]-cols[0]+1, (cols[0]+cols[-1])//2))
print('键盘亮区 y(屏): %d..%d' % (150+rows[0], 150+rows[-1]))
print('屏幕中心 240；面板 40..440 中心 240；EEZ 设计位 60..420')
