import os
import subprocess

import logging
from string import join

from pogom.utils import get_args

log = logging.getLogger(__name__)

path_icons = os.path.join('static', 'icons')
path_images = os.path.join('static', 'images')
path_gym = os.path.join(path_images, 'gym')
path_raid = os.path.join(path_images, 'raid')
path_generated = os.path.join(path_images, 'generated')

egg_images = {
    1: 'egg_normal.png',
    2: 'egg_normal.png',
    3: 'egg_rare.png',
    4: 'egg_rare.png',
    5: 'egg_legendary.png'
}


def get_gym_icon(team, level, raidlevel, pkm, is_in_battle, is_ex_raid_eligible):
    init_image_dir()
    level = int(level)

    args = get_args()
    if not args.generate_images:
        return default_gym_image(team, level, raidlevel, pkm)

    subject_lines = []
    badge_lines = []
    if pkm and pkm != 'null':
        # Gym with ongoing raid
        out_filename = os.path.join(path_generated, "{}_L{}_R{}_P{}.png".format(team, level, raidlevel, pkm))
        subject_lines = draw_subject(os.path.join(path_icons, '{}.png'.format(pkm)), 64)
        badge_lines.extend(draw_badge(80, 15, 15, "white", "black", raidlevel))
        if level > 0:
            badge_lines.extend(draw_badge(80, 80, 15, "black", "white", level))
    elif raidlevel:
        # Gym with upcoming raid (egg)
        raidlevel = int(raidlevel)
        out_filename = os.path.join(path_generated, "{}_L{}_R{}.png".format(team, level, raidlevel))
        subject_lines = draw_subject(os.path.join(path_raid, egg_images[raidlevel]), 36)
        badge_lines.extend(draw_badge(80, 15, 15, "white", "black", raidlevel))
        if level > 0:
            badge_lines.extend(draw_badge(80, 80, 15, "black", "white", level))
    elif level > 0:
        # Occupied gym
        out_filename = os.path.join(path_generated, '{}_L{}.png'.format(team, level))
        badge_lines.extend(draw_badge(80, 80, 15, "black", "white", level))
    else:
        # Neutral gym
        return os.path.join(path_gym, '{}.png'.format(team))

    # Battle Badge
    if is_in_battle:
        subject_lines.append('-gravity center ( {} -resize 84x84 ) -geometry +0+0 -composite'.format(
            os.path.join(path_images, 'boom.png')))
        out_filename = out_filename.replace('.png', '_B.png')

    # Ex Raid Badge
    if is_ex_raid_eligible:
        subject_lines.append('-gravity center ( {} -resize 50x50 ) -geometry +0+0 -composite'.format(
            os.path.join(path_images, 'exraid.png')))
        out_filename = out_filename.replace('.png', '_Ex.png')

    if not os.path.isfile(out_filename):
        gym_image = os.path.join('static', 'images', 'gym', '{}.png'.format(team))
        font = os.path.join('static', 'Arial Black.ttf')
        cmd = 'convert {} {} -gravity center -font "{}" -pointsize 25 {} {}'.format(gym_image, join(subject_lines),
                                                                                    font, join(badge_lines),
                                                                                    out_filename)
        if os.name != 'nt':
            cmd = cmd.replace(" ( ", " \( ").replace(" ) ", " \) ")
        subprocess.call(cmd, shell=True)
    return out_filename


def draw_subject(image, size, gravity='north'):
    lines = []
    lines.append(
        '-gravity {} ( {} -resize {}x{} ( +clone -background black -shadow 80x3+5+5 ) +swap -background none -layers merge +repage ) -geometry +0+0 -composite'.format(
            gravity, image, size, size))
    return lines


def draw_badge(x, y, r, fill_col, text_col, text):
    lines = []
    lines.append('-fill {} -stroke black -draw "circle {},{} {},{}"'.format(fill_col, x, y, x + r, y))
    lines.append('-fill {} -draw "text {},{} \'{}\'"'.format(text_col, x - 48, y - 49, text))
    return lines


def init_image_dir():
    if not os.path.isdir(path_generated):
        try:
            os.makedirs(path_generated)
        except OSError as exc:
            if not os.path.isdir(path_generated):
                raise

def default_gym_image(team, level, raidlevel, pkm):
    path = path_gym
    if pkm and pkm != 'null':
        icon = "{}_{}.png".format(team, pkm)
        path = path_raid
    elif raidlevel:
        icon = "{}_{}_{}.png".format(team, level, raidlevel)
    elif level:
        icon = "{}_{}.png".format(team, level)
    else:
        icon = "{}.png".format(team)

    return os.path.join(path, icon)
