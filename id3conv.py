#!/usr/bin/env python

import argparse
import inspect
import eyed3
import eyed3.id3
from eyed3.id3.tag import TagException
from eyed3.id3.frames import Frame
import os

def remove_unknown_frames(audiofile):
    if audiofile.tag is None:
        return
    for frame in audiofile.tag.frame_set:
        if isinstance(frame, Frame) and frame.header.id.startswith('TXXX'):
            audiofile.tag.frame_set.remove(frame.id)

def find_mp3_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                yield os.path.join(root, file)

def convertID3Encoding(audiofile, backup = False):
    tag = audiofile.tag
    if not tag:
        return
    for prop, value in inspect.getmembers(tag):
        if not isinstance(value, str):
            continue
        try:
            # ID3 tag (encoded in cp932) is decoded in Latin-1 by 'decodeUnicode' function
            # note: don't specify 'shift_jis' because fails to decode platform dependent characters
            setattr(tag, prop, value.encode('latin1').decode('cp932'))
        except:
            pass

    version = tag.version
    if tag.isV1() or version == eyed3.id3.ID3_V2_2:
        version = (2, 3, 0)

    has_error = False
    try:
        tag.save(encoding = 'utf-16', version = version, backup = backup)
    except TagException as e:
        print(e)
        has_error = True
        # ここで不明なフレームを処理することができる
        remove_unknown_frames(audiofile)
        print(f"'{filename}' is converted after removing unknown frames")
    
    if has_error:
        has_error = False
        try:
            tag.save(encoding = 'utf-16', version = version, backup = backup)
        except TagException as e:
            print(e)
            has_error = True

    if has_error:
        try:
            # sometime fails to save tag due to using tags supported in ID3v2.4
            tag.save(encoding = 'utf-16', version = (2, 4, 0), backup = backup)
        except TagException as e:
            print(e)
            raise Exception(e)

parser = argparse.ArgumentParser(description = 'convert ID3 tags of MP3 files from Latin-1 to UTF-16')
parser.add_argument('file', nargs = '+',
                    help = 'files to be converted')
parser.add_argument('--backup', action = 'store_true',
                    help = "backup file will be made in the same directory with '.orig' extentions")
args = parser.parse_args()

def process_file(filename):
    audiofile = eyed3.load(filename)
    if audiofile != None:
        convertID3Encoding(audiofile, args.backup)
        print("'%s' is converted" % filename)
    else:
        print("'%s' is skipped" % filename)

for path in args.file:
    if os.path.isdir(path):
        for filename in find_mp3_files(path):
            process_file(filename)
    else:
        process_file(path)