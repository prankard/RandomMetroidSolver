#!/usr/bin/python3

import argparse, os.path, json, sys, shutil, random, subprocess

from itemrandomizerweb.RandomRandomizer import Randomizer
from graph_locations import locations as graphLocations
from graph_access import vanillaTransitions, vanillaBossesTransitions, GraphUtils

from parameters import Knows, easy, medium, hard, harder, hardcore, mania, text2diff, diff2text
from utils import PresetLoader
from rom_patches import RomPatches
from rom import RomPatcher, FakeROM
from utils import loadRandoPreset
from solver import RandoSolver
import log, db

majorsSplits = ['Full', 'Major', 'Chozo']

parser = argparse.ArgumentParser(description="Random Metroid Randomizer")
parser.add_argument('--param', '-p', help="the input parameters", nargs='?',
                    default=None, dest='paramsFileName')
parser.add_argument('--rom', '-r', help="the vanilla ROM",
                    dest='rom', nargs='?', default=None)
parser.add_argument('--seed', '-s', help="randomization seed to use", dest='seed',
                    nargs='?', default=0, type=int)
parser.add_argument('--majorsSplit',
                    help="how to split majors/minors: Full, Major, Chozo",
                    dest='majorsSplit', nargs='?', choices=majorsSplits, default='Full')
parser.add_argument('--suitsRestriction',
                    help="no suits in early game",
                    dest='suitsRestriction', nargs='?', const=True, default=False)
parser.add_argument('--startLocation', help="Name of the Access Point to start from",
                    dest='startAP', nargs='?', default="Landing Site",
                    choices=GraphUtils.getStartAccessPointNames())
parser.add_argument('--ext_stats', help="dump extended stats SQL", nargs='?', default=None, dest='extStatsFilename')
parser.add_argument('--vcr', help="Generate VCR output file", dest='vcr', action='store_true')
args = parser.parse_args()

if args.rom == None:
    print("Need --rom parameter")
    sys.exit(-1)

if args.paramsFileName != None:
    PresetLoader.factory(args.paramsFileName).load()
    preset = os.path.splitext(os.path.basename(args.paramsFileName))[0]
else:
    preset = 'default'

# add patches
RomPatches.ActivePatches = RomPatches.Total
RomPatches.ActivePatches.remove(RomPatches.BlueBrinstarBlueDoor)
RomPatches.ActivePatches += GraphUtils.getGraphPatches(args.startAP)
#RomPatches.ActivePatches += RomPatches.VariaTweaks

transitions = vanillaTransitions + vanillaBossesTransitions
while True:
    # randomize items / locs
    randomizer = Randomizer(args.seed, graphLocations, transitions, args.majorsSplit, args.suitsRestriction, args.startAP, args.vcr)
    #randomizer.test()
    (itemLocs, seed) = randomizer.randomize()

    if itemLocs == None:
        if args.seed != 0:
            print("Can't randomize seed {}".format(args.seed))
            sys.exit(-1)
        else:
            # rerool a new seed
            continue

    # call solver to validate the seed
    solver = RandoSolver(args.majorsSplit, args.startAP, randomizer.areaGraph, graphLocations[:])
    if(solver.solveRom() == -1):
        print("ERROR: unsolvable seed with real solver")
        if args.seed == 0:
            continue
        else:
            sys.exit(1)
    else:
        print("seed {} validated by the real solver".format(seed))
        break

# patch rom
romFileName = args.rom
baseOutFileName = 'VARIA_Randomizer_FX{}_{}'.format(seed, preset)
outFileName = baseOutFileName + '.sfc'

# check if out file already exists:
if os.path.exists(outFileName):
    print("ERROR: {} already exists".format(outFileName))
    sys.exit(-1)

shutil.copyfile(romFileName, outFileName)

romPatcher = RomPatcher(outFileName)
romPatcher.writeItemsLocs(itemLocs)
# write standard patches and layout
romPatcher.applyIPSPatches(args.startAP, noVariaTweaks=True)
romPatcher.commitIPS()
romPatcher.end()

print("Rom generated: {}".format(baseOutFileName))

if args.extStatsFilename != None:
    # gen ext stats
    parameters = {
        'preset': preset,
        'area': False,
        'boss': False,
        'majorsSplit': args.majorsSplit,
        'startAP': 'Landing Site',
        'gravityBehaviour': 'Balanced',
        'nerfedCharge': False,
        'maxDifficulty': 'harder', # for prog speed stats (no difficulty cap)
        'progSpeed': 'rerandom',
        'morphPlacement': 'early', # 'normal',
        'suitsRestriction': True,
        'progDiff': 'normal',
        'superFunMovement': False,
        'superFunCombat': False,
        'superFunSuit': False
    }

    locsItems = {}
    for itemLoc in itemLocs:
        locName = itemLoc["Location"]["Name"]
        itemType = itemLoc["Item"]["Type"]
        locsItems[locName] = itemType

    with open(args.extStatsFilename, 'a') as extStatsFile:
        db.DB.dumpExtStatsItems(parameters, locsItems, extStatsFile)
