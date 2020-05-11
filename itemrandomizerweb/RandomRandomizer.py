import sys, time, copy, random
from datetime import datetime

from parameters import Knows, isBossKnows, Settings, samus, infinity, god
from smbool import SMBool
from helpers import Bosses
from graph import AccessGraph
from graph_access import accessPoints, GraphUtils, getAccessPoint
from smboolmanager import SMBoolManager
from itemrandomizerweb.Items import ItemManager
from vcr import VCR
import log, logging

class Randomizer(object):
    # locations : items locations
    def __init__(self, seed, locations, graphTransitions, majorsSplit, suitsRestriction, startAP, vcr=False):
        self.vcr = VCR(str(seed), 'rando') if vcr == True else None
        self.majorsSplit = majorsSplit
        self.suitsRestriction = suitsRestriction
        self.startAP = startAP

        self.errorMsg = ''
        self.areaGraph = AccessGraph(accessPoints, graphTransitions, True, None)
        # process settings
        self.log = log.get('Rando')

        self.smbm = SMBoolManager()

        self.bossLocations = [loc for loc in locations if 'Boss' in loc['Class']]

        # vanilla items
        if self.majorsSplit == 'Full':
            self.majorLocations = [loc for loc in locations if 'Boss' not in loc['Class']]
            self.minorLocations = []

            self.itemPoolMajor = ['Bomb', 'Charge', 'Ice', 'HiJump', 'SpeedBooster', 'Wave', 'Spazer', 'SpringBall', 'Varia', 'Plasma', 'Grapple', 'Morph', 'Gravity', 'XRayScope', 'SpaceJump', 'ScrewAttack']
            for _ in range(4):
                self.itemPoolMajor.append('Reserve')
            for _ in range(14):
                self.itemPoolMajor.append('ETank')
            for _ in range(46):
                self.itemPoolMajor.append('Missile')
            for _ in range(10):
                self.itemPoolMajor.append('Super')
            for _ in range(10):
                self.itemPoolMajor.append('PowerBomb')
            #for _ in range(61):
            #    self.itemPoolMajor.append('Nothing')

            self.itemPoolMinor = []
        elif self.majorsSplit == 'Major':
            self.majorLocations = [loc for loc in locations if "Major" in loc["Class"]]
            self.minorLocations = [loc for loc in locations if "Minor" in loc["Class"]]

            self.itemPoolMinor = []
            self.itemPoolMajor = ['Bomb', 'Charge', 'Ice', 'HiJump', 'SpeedBooster', 'Wave', 'Spazer', 'SpringBall', 'Varia', 'Plasma', 'Grapple', 'Morph', 'Gravity', 'XRayScope', 'SpaceJump', 'ScrewAttack']
            for _ in range(4):
                self.itemPoolMajor.append('Reserve')
            for _ in range(14):
                self.itemPoolMajor.append('ETank')
            for _ in range(46):
                self.itemPoolMinor.append('Missile')
            for _ in range(10):
                self.itemPoolMinor.append('Super')
            for _ in range(10):
                self.itemPoolMinor.append('PowerBomb')
        else:
            self.majorLocations = [loc for loc in locations if "Chozo" in loc["Class"]]
            self.minorLocations = [loc for loc in locations if "Chozo" not in loc["Class"] and "Boss" not in loc["Class"]]

            self.itemPoolMinor = []
            self.itemPoolMajor = ['Bomb', 'Charge', 'Ice', 'HiJump', 'SpeedBooster', 'Wave', 'Spazer', 'SpringBall', 'Varia', 'Plasma', 'Grapple', 'Morph', 'Gravity', 'XRayScope', 'SpaceJump', 'ScrewAttack']
            for _ in range(1):
                self.itemPoolMajor.append('Reserve')
            for _ in range(3):
                self.itemPoolMajor.append('ETank')
            for _ in range(2):
                self.itemPoolMajor.append('Missile')
            for _ in range(2):
                self.itemPoolMajor.append('Super')
            for _ in range(1):
                self.itemPoolMajor.append('PowerBomb')

            for _ in range(3):
                self.itemPoolMinor.append('Reserve')
            for _ in range(11):
                self.itemPoolMinor.append('ETank')
            for _ in range(44):
                self.itemPoolMinor.append('Missile')
            for _ in range(8):
                self.itemPoolMinor.append('Super')
            for _ in range(9):
                self.itemPoolMinor.append('PowerBomb')

        for loc in self.bossLocations:
            loc['itemName'] = 'Boss'

        self.seed = seed

    def randomize(self):
        count = 0
        randomSeed = random.randrange(sys.maxsize)
        print("random seed: {}".format(randomSeed))
        random.seed(randomSeed)

        start = datetime.now()

        while True:
            count += 1

            # randomize items order
            if self.seed == 0:
                seed = random.randint(0, sys.maxsize)
            else:
                if count > 1:
                    # couldn't randomize the given seed
                    return (None, self.seed)
                seed = self.seed
            random.seed(seed)

            itemPoolMajor = self.itemPoolMajor[:]
            random.shuffle(itemPoolMajor)
            itemPoolMinor = self.itemPoolMinor[:]
            random.shuffle(itemPoolMinor)

            # add items
            for (loc, item) in zip(self.majorLocations, itemPoolMajor):
                loc["itemName"] = item
            for (loc, item) in zip(self.minorLocations, itemPoolMinor):
                loc["itemName"] = item

            # check if seed is beatable
            if self.isBeatable() and self.checkRestrictions():
                end = datetime.now()
                duration = int((end - start).microseconds/1000)
                print("{}: found a beatable seed with mini solver: {} in {}ms after {} tries".format(time.asctime(), seed, duration, count))
                if self.vcr != None:
                    self.vcr.outFileName = '{}.rando.vcr'.format(seed)
                    self.vcr.dump()
                return (self.getItemLocs(), seed)
            else:
                # if we couldn't find a valid seed after 10000 tries, reroll a new seed for the random module
                if count % 10000 == 0:
                    print("{}: {} tries done".format(time.asctime(), count))
                    return (None, seed)

    def checkRestrictions(self):
        if self.suitsRestriction == False:
            return True
        else:
            # check that there's no varia ou gravity in given list of locations
            for loc in self.majorLocations:
                if loc['GraphArea'] == 'Crateria' and loc['itemName'] in ['Varia', 'Gravity']:
                    print("suits restrictions nok")
                    return False
            print("suits restrictions ok")
            return True

    def getItemLocs(self):
        itemLocs = []
        for loc in self.majorLocations:
            itemName = loc['itemName']
            itemLocs.append({'Location': loc, 'Item': ItemManager.getItem(itemName)})
        for loc in self.minorLocations:
            itemName = loc['itemName']
            itemLocs.append({'Location': loc, 'Item': ItemManager.getItem(itemName)})
        return itemLocs

    def isBeatable(self):
        Bosses.reset()
        self.smbm.resetItems()

        for loc in self.majorLocations:
            loc['difficulty'] = None
        for loc in self.minorLocations:
            loc['difficulty'] = None
        for loc in self.bossLocations:
            loc['difficulty'] = None

        locations = self.majorLocations[:] + self.minorLocations[:] + self.bossLocations[:]
        #print("len locations: {}".format(len(locations)))

        if self.vcr != None:
            self.vcr.tape = []

        while True:
            if len(locations) == 0:
                return True

            self.areaGraph.getAvailableLocations(locations, self.smbm, infinity, self.startAP)

            for loc in locations:
                if loc['difficulty'].bool == True:
                    if 'PostAvailable' in loc:
                        self.smbm.addItem(loc['itemName'])
                        postAvailable = loc['PostAvailable'](self.smbm)
                        self.smbm.removeItem(loc['itemName'])

                        loc['difficulty'] = self.smbm.wand(loc['difficulty'], postAvailable)

            toCollect = [loc for loc in locations if loc['difficulty'].bool == True]
            if len(toCollect) == 0:
                #print("len remaining locations: {}".format(len([loc for loc in locations if loc['difficulty'].bool == False])))
                return False

            for loc in toCollect:
                self.smbm.addItem(loc['itemName'])
                if 'Pickup' in loc:
                    loc['Pickup']()
                if self.vcr != None:
                    self.vcr.addLocation(loc['Name'], loc['itemName'])

            #print("visited locs: {}".format([loc['Name'] for loc in locations if loc['difficulty'].bool == True]))
            locations = [loc for loc in locations if loc['difficulty'].bool != True]
