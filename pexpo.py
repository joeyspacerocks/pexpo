#!/usr/bin/python

import os
import sys
import StringIO
import argparse
import json
import zipfile
from PIL import Image, ImageColor
import xml.etree.cElementTree as ET


# TODO: compose multiple layers
def compose_image(indexes, archive):
	file = 'layer' + str(indexes[0]) + '.png'
	return Image.open(StringIO.StringIO(archive.read(file)))

def aggregate_sprites(sprites, data):
	for d in data:
		for s in d['sprites']:
			sprites.append(s)
			if 'mask' in s: sprites.append(s['mask'])

def pack_images(filename, data):
	sprites = []
	aggregate_sprites(sprites, data['anims'])
	aggregate_sprites(sprites, data['tiles'])

	# sort sprites by height
	sprites.sort(key = lambda s: s['image'].size[1], reverse = True)
	
	# pack
	
	dest = Image.new("RGBA", (256, 256))
	mask = Image.new("1", (256, 256))

	dp = dest.load()
	mp = mask.load()

# 	masq.resize(image_width, 1);
#     dest.resize(image_width, 1);
    
	for s in sprites:
		idx = s['image'].size[0]
		idy = s['image'].size[1]
      
#       assert(idx <= image_width);
      
		found = False
      
		for ty in range(2048):
			if found: break

#         if(ty + idy > dest.dat.size()) {
#           masq.resize(image_width, ty + idy);
#           dest.resize(image_width, ty + idy);
#         }

			for tx in range(dest.size[0] - idx):
				if found: break
	      	
				valid = not(mp[tx, ty] or mp[tx, ty + idy - 1] or mp[tx + idx - 1, ty] or mp[tx + idx - 1, ty + idy - 1])
          
				if valid:
					for ity in range(idy):
						if not valid: break
						for itx in range(idx):
							if not valid: break
							if mp[tx + itx, ty + ity]:
								valid = False

				if valid:
					dest.paste(s['image'], (tx, ty))
					mask.paste(int(True), (tx, ty, tx + idx, ty + idy))

					s["x"] = tx
					s["y"] = ty
					s["w"] = idx
					s["h"] = idy

					found = True

	# write image

	dest.save(filename, 'png')

def write_meta(filename, imagefile, data):
	root = ET.Element("spritesheet", image=imagefile)

	aroot = ET.SubElement(root, "anims")
	for a in data['anims']:
		anode = ET.SubElement(aroot, "a", name=a['name'])
		for s in a["sprites"]:
			ET.SubElement(anode, "s", x=str(s['x']), y=str(s['y']), w=str(s['w']), h=str(s['h']), d=str(s['duration']))
			if 'mask' in s:
				mnode = ET.SubElement(snode, "mask")
				ET.SubElement(mnode, "s", x=str(s['x']), y=str(s['y']), w=str(s['w']), h=str(s['h']))

	sroot = ET.SubElement(root, "sprites")
	for t in data['tiles']:
		snode = ET.SubElement(sroot, "sprite", name=t['name'])
		for s in t["sprites"]:
			mnode = ET.SubElement(snode, "s", x=str(s['x']), y=str(s['y']), w=str(s['w']), h=str(s['h']))
			if 'mask' in s:
				mask = s['mask']
				mnode.set('mx', str(mask['x']))
				mnode.set('my', str(mask['y']))

	tree = ET.ElementTree(root)
	tree.write(filename)

def grab_tiles(data, duration, img, mask, base, count, tw, th):
	img_w = img.size[0]
	tpr = img_w / tw

	x = (base % tpr) * tw
	y = (base / tpr) * th

	sprites = []
	data['sprites'] = sprites
	
	for i in range(count):
		box = (x, y, x + tw, y + th)
		sprite = {}
		sprites.append(sprite)
		sprite['image'] = img.crop(box)
		if mask is not None:
			sprite['mask'] = { 'image': mask.crop(box) }
		sprite['duration'] = duration
		x += tw
		if x >= img_w:
			x = 0
			y += th

def generate_tileset(path, file, outpng):
	archive = zipfile.ZipFile(os.path.join(path, file), 'r')
	src = json.loads(archive.read('docData.json'))

	tileset = src['tileset']
	tw = tileset['tileWidth']
	th = tileset['tileHeight']
	per_row = tileset['tilesWide']
	tile_count = tileset['numTiles']
	
	iw = per_row * tw
	ih = (tile_count / per_row) * th

	dest = Image.new("RGBA", (iw, ih))

	tx = 0
	ty = 0
	for i in range(tile_count):
		tile_img = Image.open(StringIO.StringIO(archive.read("tile%d.png" % i)))
		dest.paste(tile_img, (tx * tw, ty * th))
		tx += 1
		if tx >= per_row:
			tx = 0
			ty += 1

	dest.save(outpng, 'png')


def compile_sprite_data(data, path, file):
	archive = zipfile.ZipFile(os.path.join(path, file), 'r')
	src = json.loads(archive.read('docData.json'))

	canvas = src['canvas']
	anims = src['animations']

	w = canvas['width']
	h = canvas['height']
	tw = canvas['tileWidth']
	th = canvas['tileHeight']
	
	if tw == 0 or tw > w: tw = w
	if th == 0 or th > h: th = h

	# compose all visible layers, except for the magic 'mask' layer
	
	layers = []
	masks = []
	for i, layer in canvas['layers'].items():
		if not layer['hidden']:
			if layer['name'] == 'mask':
				masks.append(i)
			else:
				layers.append(i)
	
	img = compose_image(layers, archive)
	if len(masks) > 0:
		mask = compose_image(masks, archive)
	else:
		mask = None
	
	name = os.path.splitext(file)[0]

	if len(anims) > 0:
		print ' - ' + name + ' - export animations (' + str(len(anims)) + ')'
		for ai in anims.keys():
			anim = anims[ai]
			base = anim['baseTile']
			length = anim['length']
			duration = anim['frameDuration']
			
			out = {}
			out['name'] = name + '-' + anim['name']
			grab_tiles(out, duration, img, mask, base, length, tw, th)
			data['anims'].append(out)
	else:
		print ' - ' + name + ' - export tilemap'
		out = { 'name': name }
		grab_tiles(out, 0, img, mask, 0, (w / tw) * (h / th), tw, th)
		data['tiles'].append(out)

	return data

def main(script, argv):
	parser = argparse.ArgumentParser(description='Export PNGs and meta-data from PyxelEdit files.')
	parser.add_argument('path', help='path to pyxel files (directory or single file)', metavar='<path>')
	parser.add_argument('-t', '--tileset', help='generate tileset instead of spritesheet', action='store_true', dest='tileset')
	parser.add_argument('-o', '--out', help='filename of assembled PNG', required=True, metavar='<file>', dest='outpng')

	args = parser.parse_args()
	path = args.path
	
	if args.tileset:
		generate_tileset(os.path.dirname(path), os.path.basename(path), args.outpng)
		
	else:
		data = { 'anims':[], 'tiles':[] }

		if os.path.isfile(path):
			compile_sprite_data(data, os.path.dirname(path), os.path.basename(path))
				
		else:
			for i in os.listdir(path):
				if i.endswith(".pyxel"): 
					compile_sprite_data(data, path, i)
	
		pack_images(args.outpng, data)
		write_meta(os.path.splitext(args.outpng)[0] + '.xml', os.path.basename(args.outpng), data)


if __name__ == '__main__':
    sys.exit(main(sys.argv[0], sys.argv[1:]))
