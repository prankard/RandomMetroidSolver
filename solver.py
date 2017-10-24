#!/usr/bin/python

# https://itemrando.supermetroid.run/randomize

import sys, struct, math

# the difficulties for each technics
from parameters import *

def getItem(romFile, address, visibility):
    # return the hex code of the object at the given address

    romFile.seek(address, 0)
    # value is in two bytes
    value1 = struct.unpack("B", romFile.read(1))
    value2 = struct.unpack("B", romFile.read(1))

    # match itemVisibility with
    # | Visible -> 0
    # | Chozo -> 0x54 (84)
    # | Hidden -> 0xA8 (168)
    if visibility == 'Visible':
        return hex(value2[0]*256+(value1[0]-0))
    elif visibility == 'Chozo':
        return hex(value2[0]*256+(value1[0]-84))
    elif visibility == 'Hidden':
        return hex(value2[0]*256+(value1[0]-168))
    else:
        # crash !
        manger.du(cul)

# we have to compare booleans, but with a weight (the difficulty)
# a and b type is: (bool, weight)
# if true, add given difficulty to output
def wand2(a, b, difficulty=0):
    if a[0] is True and b[0] is True:
        return (True, a[1] + b[1] + difficulty)
    else:
        return (False, 0)

def wand(a, b, c=None, d=None, difficulty=0):
    if c is None and d is None:
        ret = wand2(a, b)
    elif c is None:
        ret = wand2(wand2(a, b), d)
    elif d is None:
        ret = wand2(wand2(a, b), c)
    else:
        ret = wand2(wand2(wand2(a, b), c), d)

    if ret[0] is True:
        return (ret[0], ret[1] + difficulty)
    else:
        return (False, 0)

def wor2(a, b, difficulty=0):
    if a[0] is True and b[0] is True:
        return (True, min(a[1], b[1]) + difficulty)
    elif a[0] is True:
        return (True, a[1] + difficulty)
    elif b[0] is True:
        return (True, b[1] + difficulty)
    else:
        return (False, 0)

def wor(a, b, c=None, d=None, difficulty=0):
    if c is None and d is None:
        ret = wor2(a, b)
    elif c is None:
        ret = wor2(wor2(a, b), d)
    elif d is None:
        ret = wor2(wor2(a, b), c)
    else:
        ret = wor2(wor2(wor2(a, b), c), d)

    if ret[0] is True:
        return (ret[0], ret[1] + difficulty)
    else:
        return (False, 0)

# check items and compute difficulty
# the second parameter returned is the difficulty:
def haveItemCount(items, item, count):
    return items.count(item) >= count

def haveItem(items, item, difficulty=0):
    return (item in items, difficulty)

def itemCount(items, item):
    return items.count(item)

def itemCountOk(items, item, count, difficulty=0):
    return (itemCount(items, item) >= count, difficulty)

def itemCountOkList(items, item, difficulties):
    # get a list: [(2, difficulty=hard), (4, difficulty=medium), (6, difficulty=easy)]
    difficulties = difficulties[:] # copy
    difficulty = difficulties.pop(0)
    result = itemCountOk(items, item, difficulty[0], difficulty=difficulty[1])
    while len(difficulties) > 0:
        difficulty = difficulties.pop(0)
        result = wor(result, itemCountOk(items, item, difficulty[0], difficulty=difficulty[1]))
    return result

def energyReserveCount(items):
    return itemCount(items, 'ETank') + itemCount(items, 'Reserve')

def energyReserveCountOk(items, count, difficulty=0):
    return (energyReserveCount(items) >= count, difficulty)

def energyReserveCountOkList(items, difficulties):
    # get a list: [(2, difficulty=hard), (4, difficulty=medium), (6, difficulty=easy)]
    difficulties = difficulties[:] # copy
    difficulty = difficulties.pop(0)
    result = energyReserveCountOk(items, difficulty[0], difficulty=difficulty[1])
    while len(difficulties) > 0:
        difficulty = difficulties.pop(0)
        result = wor(result, energyReserveCountOk(items, difficulty[0], difficulty=difficulty[1]))
    return result

def heatProof(items):
    return haveItem(items, 'Varia')

def canHellRun(items):
    if heatProof(items)[0]:
        return (True, easy)
    elif energyReserveCount(items) >= 3:
        return energyReserveCountOkList(items, hellRuns['Rest'])
    else:
        return (False, 0)

def canFly(items):
    if haveItem(items, 'SpaceJump')[0]:
        return (True, easy)
    elif haveItem(items, 'Morph')[0] and haveItem(items, 'Bomb')[0] and knowsInfiniteBombJump[0]:
        return knowsInfiniteBombJump
    else:
        return (False, 0)

def canFlyDiagonally(items):
    if haveItem(items, 'SpaceJump')[0]:
        return (True, easy)
    elif haveItem(items, 'Morph')[0] and haveItem(items, 'Bomb')[0] and knowsDiagonalBombJump[0]:
        return knowsDiagonalBombJump
    else:
        return (False, 0)

def canUseBombs(items, difficulty=0):
    return wand(haveItem(items, 'Morph'), haveItem(items, 'Bomb'), difficulty=difficulty)

def canOpenRedDoors(items):
    return wor(haveItem(items, 'Missile'), haveItem(items, 'Super'))

def canOpenGreenDoors(items):
    return haveItem(items, 'Super')

def canOpenYellowDoors(items):
    return wand(haveItem(items, 'Morph'), haveItem(items, 'PowerBomb'))

def canUsePowerBombs(items):
    return canOpenYellowDoors(items)

def canDestroyBombWalls(items):
    return wor(wand(haveItem(items, 'Morph'),
                    wor(haveItem(items, 'Bomb'),
                        haveItem(items, 'PowerBomb'))),
               haveItem(items, 'ScrewAttack'))

def canEnterAndLeaveGauntlet(items):
    return wand(wor(canFly(items), wand(haveItem(items, 'HiJump'), knowsHiJumpGauntletAccess), haveItem(items, 'SpeedBooster')),
                wor(wand(canUseBombs(items), knowsGauntletWithBombs),
                    wand(canUsePowerBombs(items), itemCountOk(items, 'PowerBomb', 2), knowsGauntletWithPowerBombs),
                    haveItem(items, 'ScrewAttack'),
                    wand(haveItem(items, 'SpeedBooster'), canUsePowerBombs(items), energyReserveCountOk(items, 2), wand(knowsSimpleShortCharge, knowsGauntletEntrySpark))))

def canPassBombPassages(items):
    return wor(canUseBombs(items), canUsePowerBombs(items))

def canAccessRedBrinstar(items):
    return wand(haveItem(items, 'Super'),
                wor(wand(canDestroyBombWalls(items),
                         haveItem(items, 'Morph')),
                    canUsePowerBombs(items)))

def canAccessKraid(items):
    return wand(canAccessRedBrinstar(items),
                canPassBombPassages(items),
                wor(knowsEarlyKraid,
                    haveItem(items, 'HiJump'),
                    canFly(items)))

def canAccessWs(items):
    return wand(canUsePowerBombs(items),
                haveItem(items, 'Super'),
                wor(haveItem(items, 'Grapple'),
                    haveItem(items, 'SpaceJump'),
                    wor(knowsContinuousWallJump,
                        wand(canUseBombs(items), knowsDiagonalBombJump),
                        wand(haveItem(items, 'SpeedBooster'), knowsSimpleShortCharge))))

def canAccessHeatedNorfair(items):
    return wand(canAccessRedBrinstar(items), canHellRun(items))

def canAccessCrocomire(items):
    return wor(wand(canAccessHeatedNorfair(items), wor(haveItem(items, 'Wave'), knowsGreenGateGlitch)),
               wand(canAccessKraid(items), # FIXME : knowsEarlyKraid "trick" is now entangled with crocomire access
                    canUsePowerBombs(items), 
                    haveItem(items, 'SpeedBooster'),
                    energyReserveCountOk(items, 2)))

def canAccessLowerNorfair(items):
    return wand(canAccessHeatedNorfair(items), # FIXME : hell runs difficulty settings affect lower norfair access with a 'and' condition...on paper this is bad, but you do want some etanks before going there
                canUsePowerBombs(items),
                haveItem(items, 'Varia'),
                wor(wand(haveItem(items, 'HiJump'), knowsLavaDive),
                    wand(haveItem(items, 'Gravity'), knowsGravityJump),
                    wand(haveItem(items, 'Gravity'), haveItem(items, 'SpaceJump'))))

def canPassWorstRoom(items):
    return wand(canAccessLowerNorfair(items),
                wor(canFly(items),
                    wand(haveItem(items, 'Ice'), haveItem(items, 'Charge'), knowsWorstRoomIceCharge),
                    haveItem(items, 'HiJump', knowsWorstRoomHiJump)))

def canAccessOuterMaridia(items):
    # even harder if without gravity and without stronger gun
    return wand(canAccessRedBrinstar(items),
                canUsePowerBombs(items),
                wor(haveItem(items, 'Gravity'),
                    wor(wand(haveItem(items, 'HiJump'),
                             haveItem(items, 'Ice'),
                             wor(knowsSuitlessOuterMaridiaNoGuns,
                                 wand(knowsSuitlessOuterMaridia,
                                      haveItem(items, 'SpringBall'), knowsSpringBallJump))),
                        wand(haveItem(items, 'HiJump'),
                             haveItem(items, 'Ice'),
                             wor(haveItem(items, 'Wave'),
                                 haveItem(items, 'Spazer'),
                                 haveItem(items, 'Plasma')),
                             knowsSuitlessOuterMaridia))))

def canAccessInnerMaridia(items):
    # easy regular way
    return wand(canAccessRedBrinstar(items),
                canUsePowerBombs(items),
                haveItem(items, 'Gravity'))

def canDoSuitlessMaridia(items):
    # harder way
    return wand(canAccessOuterMaridia(items),
                haveItem(items, 'Grapple'))

def canDefeatBotwoon(items):
    return wand(wor(canAccessInnerMaridia(items),
                    canDoSuitlessMaridia(items)),
                wor(wand(haveItem(items, 'Ice'),
                         knowsMochtroidClip),
                    haveItem(items, 'SpeedBooster')))

def canDefeatDraygon(items):
    return wand(canDefeatBotwoon(items),
                haveItem(items, 'Gravity'));

# returns a tuple with :
#
# - a floating point number : 0 if boss is unbeatable with
# current equipment, and an ammo "margin" (ex : 1.5 means we have 50%
# more firepower than absolutely necessary). Useful to compute boss
# difficulty when not having charge. If player has charge, the actual
# value is not useful, and is guaranteed to be > 2.
#
# - estimation of the fight duration in seconds (well not really, it
# is if you fire and land shots perfectly and constantly), giving info
# to compute boss fight difficulty
def canInflictEnoughDamages(items, bossEnergy, doubleSuper=False, charge=True, power=False, givesDrops=True):
    # TODO: handle special beam attacks ? (http://deanyd.net/sm/index.php?title=Charge_Beam_Combos)

    # http://deanyd.net/sm/index.php?title=Damage
    standardDamage = 0
    if haveItem(items, 'Charge')[0] and charge is True:
        if wand(haveItem(items, 'Ice'), haveItem(items, 'Wave'), haveItem(items, 'Plasma'))[0]:
            standardDamage = 300
        elif wand(haveItem(items, 'Wave'), haveItem(items, 'Plasma')):
            standardDamage = 250
        elif wand(haveItem(items, 'Ice'), haveItem(items, 'Plasma')):
            standardDamage = 200
        elif wand(haveItem(items, 'Plasma')):     
            standardDamage = 150
        elif wand(haveItem(items, 'Ice'), haveItem(items, 'Wave'), haveItem(items, 'Spazer')):
            standardDamage = 100
        elif wand(haveItem(items, 'Wave'), haveItem(items, 'Spazer')):
            standardDamage = 70
        elif wand(haveItem(items, 'Ice'), haveItem(items, 'Spazer')):
            standardDamage = 60
        elif wand(haveItem(items, 'Ice'), haveItem(items, 'Wave')):
            standardDamage = 60
        elif haveItem(items, 'Wave'):
            standardDamage = 50
        elif haveItem(items, 'Spazer'):
            standardDamage = 40
        elif haveItem(items, 'Ice'):
            standardDamage = 30
        else:
            standardDamage = 20

    # charge triples the damage
    chargeDPS = standardDamage * 3.0

    # missile 100 damages, super missile 300 damages, 5 missile in each extension
    missilesAmount = itemCount(items, 'Missile') * 5
    missilesDamage = missilesAmount * 100
    supersAmount = itemCount(items, 'Super') * 5
    oneSuper = 300.0
    if doubleSuper is True:
        oneSuper *= 2
    supersDamage = supersAmount * oneSuper    

    powerDamage = 0
    powerAmount = 0
    if power is True and haveItem(items, 'PowerBomb')[0]:
        # PBs come also in packs of 5
        powerAmount = itemCount(items, 'PowerBomb') * 5 
        powerDamage = powerAmount * 200

    canBeatBoss = chargeDPS > 0 or givesDrops or (missilesDamage + supersDamage + powerDamage) >= bossEnergy

    if not canBeatBoss:
        return (0, 0)
    ammoMargin = (missilesDamage + supersDamage + powerDamage) / bossEnergy
    if chargeDPS > 0:
        ammoMargin += 2

    # FIXME : these are rough estimations
    missilesDPS = 4 * 100.0
    supersDPS = 2 * 300.0
    if doubleSuper is True:
        supersDPS *= 2
    if powerDamage > 0:    
        powerDPS = 200.0 / 3
    else:
        powerDPS = 0.0
    dpsDict = { missilesDPS : (missilesAmount, 100.0), supersDPS : (supersAmount, oneSuper), powerDPS : (powerAmount, 200.0), chargeDPS : (10000, chargeDPS) } # one charged shot per second. and no boss will take more 10000 charged shots
    secs = 0
    for dps in sorted(dpsDict, reverse=True):
        amount = dpsDict[dps][0]
        one = dpsDict[dps][1]
        if dps == 0 or one == 0 or amount == 0:
            continue
        fire = min(bossEnergy / one, amount)
        secs += fire * (one / dps)
        bossEnergy -= fire * one
        if bossEnergy <= 0:
            break
    if bossEnergy > 0:
        # rely on missile drops : let's say you get 12 missiles in a minute and fire them (DPS of 20)
        secs += (bossEnergy / 20.0)
    #print('ammoMargin = ' + str(ammoMargin) + ', secs = ' + str(secs))
        
    return (ammoMargin, secs)

def computeBossDifficulty(items, ammoMargin, secs, diffTbl):
    # actual fight duration :
    rate = None
    if diffTbl.has_key('Rate'):
        rate = diffTbl['Rate']
    if rate is None:
        duration = 120.0
    else:
        duration = secs / rate
    suitsCoeff = 0.5
    if haveItem(items, 'Varia')[0]:
        suitsCoeff *= 2
    if haveItem(items, 'Gravity')[0]:
        suitsCoeff *= 2
    energy = suitsCoeff * energyReserveCount(items)
    #print('suitsCoeff = ' + str(suitsCoeff) + ', energy = ' + str(energy) + ', duration = ' + str(duration))
    energyDict = None
    if diffTbl.has_key('Energy'):
        energyDict = diffTbl['Energy']
    difficulty = medium
    # get difficulty by energy
    if energyDict:
        keyz = sorted(energyDict.keys())
        if len(keyz) > 0:
            difficulty = energyDict[keyz[0]]
            for k in keyz:
                if k > energy:
                    break
                difficulty = energyDict[k]
    # FIXME : formulas below shall be adapted to actual difficulty value 'scale' we use
    # adjust by fight duration
    difficulty *= (duration / 120)
    # and by ammo margin : 50% more is considered 'normal'
    # only augment difficulty in case of no charge, don't lower it.
    # if we have charge, ammoMargin will be > 2 (see canInflictEnoughDamages),
    # so this does not apply
    diffAdjust = (1 - (ammoMargin - 1.5))
    if diffAdjust > 1:
        difficulty *= diffAdjust
    #print('difficulty = ' + str(difficulty))
        
    return difficulty

def enoughStuffsRidley(items):
    #print('RIDLEY')
    (ammoMargin, secs) = canInflictEnoughDamages(items, 18000, doubleSuper=True, givesDrops=False)
    if ammoMargin == 0:
        return (False, 0)
    return (True, computeBossDifficulty(items, ammoMargin, secs, bossesDifficulty['Ridley']))

def enoughStuffsKraid(items):
    #print('KRAID')
    (ammoMargin, secs) = canInflictEnoughDamages(items, 1000)
    if ammoMargin == 0:
        return (False, 0)
    return (True, computeBossDifficulty(items, ammoMargin, secs, bossesDifficulty['Kraid']))    

def enoughStuffsDraygon(items):
    #print('DRAYGON')
    (ammoMargin, secs) = canInflictEnoughDamages(items, 6000)
    fight = (False, 0)
    if ammoMargin > 0:
        fight = (True, computeBossDifficulty(items, ammoMargin, secs, bossesDifficulty['Draygon']))    
    return wor(fight,
               wand(knowsDraygonGrappleKill,
                    haveItem(items, 'Grapple')),
               wand(knowsShortCharge,
                    haveItem(items, 'SpeedBooster')))

def enoughStuffsPhantoon(items):
    #print('PHANTOON')
    (ammoMargin, secs) = canInflictEnoughDamages(items, 2500, doubleSuper=True)
    if ammoMargin == 0:
        return (False, 0)
    difficulty = computeBossDifficulty(items, ammoMargin, secs, bossesDifficulty['Phantoon'])
    hasCharge = haveItem(items, 'Charge')[0]
    if hasCharge or haveItem(items, 'ScrewAttack')[0]:
        difficulty /= 1.2 # you can avoid flames        
    elif not hasCharge and itemCount(items, 'Missile') <= 2: # few missiles is harder
        difficulty *= 1.2
        
    return (True, difficulty)

def enoughStuffsMotherbrain(items):
    #print('MB')
    # MB1 can't be hit by charge beam
    (ammoMargin, secs) = canInflictEnoughDamages(items, 3000, charge=False, givesDrops=False)
    if ammoMargin == 0:
        return (False, 0)
    # we actually don't give a shit about MB1 difficulty, since we embark its health in the following calc
    (ammoMargin, secs) = canInflictEnoughDamages(items, 18000 + 3000, givesDrops=False)
    if ammoMargin == 0:
        return (False, 0)
    return (True, computeBossDifficulty(items, ammoMargin, secs, bossesDifficulty['Mother Brain']))

def enoughMinors(items, minorLocations):
    if itemsPickup == '100%':
        # need them all
        return len(minorLocations) == 0
    elif itemsPickup == 'minimal':
        return haveItemCount(items, 'Missile', 3) and haveItemCount(items, 'Super', 2) and haveItemCount(items, 'PowerBomb', 1)
    elif itemsPickup == 'normal':
        return canEndGame(items)[0]

def enoughMajors(items, majorLocations):
    # the end condition
    if itemsPickup == '100%' or itemsPickup == 'normal':
        return len(majorLocations) == 0
    elif itemsPickup == 'minimal':
        return haveItemCount(items, 'Morph', 1) and (haveItemCount(items, 'Bomb', 1) or haveItemCount(items, 'PowerBomb', 1)) and haveItemCount(items, 'ETank', 3) and haveItemCount(items, 'Varia', 1) and (haveItemCount(items, 'SpeedBooster', 1) or haveItemCount(items, 'Ice', 1)) and haveItemCount(items, 'Gravity', 1)

def canBeatKraid(items):
    return getLocation("Varia Suit")['Available'](items)

def canBeatPhantoon(items):
    return getLocation("Right Super, Wrecked Ship")['Available'](items)

def canBeatRidley(items):
    return getLocation("Energy Tank, Ridley")['Available'](items)

def canBeatDraygon(items):
    return getLocation("Space Jump")['Available'](items)

def canBeatGoldenFour(items):
    return wand(canBeatKraid(items), canBeatPhantoon(items), canBeatDraygon(items), canBeatRidley(items))

def canPassMetroids(items):
    return wand(canOpenRedDoors(items), wor(haveItem(items, 'Ice'), (haveItemCount(items, 'PowerBomb', 3), 0))) # to avoid leaving tourian to refill power bombs

def canPassZebetites(items):
    return wor(wand(haveItem(items, 'Ice'), knowsIceZebSkip), wand(haveItem(items, 'SpeedBooster'), knowsSpeedZebSkip), (canInflictEnoughDamages(items, 1100*3, charge=False, givesDrops=False) >= 1, 0)) # account for all the zebs to avoid constant refills

def canEndGame(items):
    # to finish the game you must :
    # - beat golden 4
    # - defeat metroids
    # - destroy/skip the zebetites
    # - beat Mother Brain
    return wand((canBeatGoldenFour(items)[0], 0), canPassMetroids(items), canPassZebetites(items), enoughStuffsMotherbrain(items)) # difficulty for golden 4 already accounted for by enoughMajors and enoughMinors

def getDifficulty(locations):
    # loop on the available locations depending on the collected items
    # before getting a new item, loop on all of them and get their difficulty, the next collected item is the one with the smallest difficulty, if equality between major and minor, take major first

    majorLocations = filter(lambda location: location["Class"] == "Major", locations)
    minorLocations = filter(lambda location: location["Class"] == "Minor", locations)

    visitedLocations = []
    collectedItems = []

    # with the knowsXXX conditions some roms can be unbeatable, so we have to detect it
    previous = -1
    current = 0

    print("{}: available major: {}, available minor: {}, visited: {}".format(itemsPickup, len(majorLocations), len(minorLocations), len(visitedLocations)))

    isEndPossible = False
    endDifficulty = mania
    while True:
        # actual while condition
        hasEnoughItems = enoughMajors(collectedItems, majorLocations) and enoughMinors(collectedItems, minorLocations)
        (isEndPossible, endDifficulty) = canEndGame(collectedItems)        
        if isEndPossible and hasEnoughItems:
            break
        # print(str(collectedItems))

        current = len(collectedItems)
        if current == previous:
            # we're stuck ! abort
            break
        previous = current

        # compute the difficulty of all the locations
        for loc in majorLocations:
            loc['difficulty'] = loc['Available'](collectedItems)
        enough = enoughMinors(collectedItems, minorLocations)
        if not enough:
            for loc in minorLocations:
                loc['difficulty'] = loc['Available'](collectedItems)

        # keep only the available locations
        majorAvailable = filter(lambda loc: loc["difficulty"][0] == True, majorLocations)
        if not enough:
            minorAvailable = filter(lambda loc: loc["difficulty"][0] == True, minorLocations)

        # that shouldn't happen
        if len(majorAvailable) == 0 and enough is True:
            print('ERROR: no more major item available')
            boire.dela(chiasse)

        # sort them on difficulty
        majorAvailable.sort(key=lambda loc: loc['difficulty'][1])
        if not enough:
            minorAvailable.sort(key=lambda loc: loc['difficulty'][1])

        # first take major items with no difficulty
        majorPicked = False
        while len(majorAvailable) > 0 and majorAvailable[0]["difficulty"][1] == easy:
            loc = majorAvailable.pop(0)
            majorLocations.remove(loc)
            visitedLocations.append(loc)
            collecting = items[loc["item"]]["name"]
            collectedItems.append(collecting)
            #print("collecting major : " + collecting + " at " + loc['Name'])
            majorPicked = True

        # if we take at least one major, recompute the difficulty
        if majorPicked is True:
            continue

        # if enough stuff, take the next available major
        if enough is True:
            # take first major
            loc = majorAvailable.pop(0)
            majorLocations.remove(loc)
            visitedLocations.append(loc)
            collecting = items[loc["item"]]["name"]
            collectedItems.append(collecting)
            #print("collecting major : " + collecting + " at " + loc['Name'])
        else:
            if len(majorAvailable) == 0:
                nextMajorDifficulty = mania * 10
            else:
                nextMajorDifficulty = majorAvailable[0]["difficulty"][1]

            # take the minors easier than the next major, check if we don't get too much stuff
            minorPicked = False
            while len(minorAvailable) > 0 and minorAvailable[0]["difficulty"][1] < nextMajorDifficulty and not enoughMinors(collectedItems, minorLocations):
                loc = minorAvailable.pop(0)
                minorLocations.remove(loc)
                visitedLocations.append(loc)
                collecting = items[loc["item"]]["name"]
                collectedItems.append(collecting)
                # print("collecting minor : " + collecting + " at " + loc['Name'])
                minorPicked = True

            # if we take at least one minor, recompute the difficulty
            if minorPicked is True:
                continue

            # take the next available major
            if len(majorAvailable) > 0:
                loc = majorAvailable.pop(0)
                majorLocations.remove(loc)
                visitedLocations.append(loc)
                collecting = items[loc["item"]]["name"]
                collectedItems.append(collecting)
                #print("collecting major : " + collecting + " at " + loc['Name'])

    if isEndPossible:
        visitedLocations.append({
            'item' : 'The End',
            'Name' : 'The End',
            'Area' : 'The End',
            'difficulty' : (True, endDifficulty)
        })
    # print generated path
    if displayGeneratedPath is True:
        print("Generated path:")
        print('{:>50}: {:>12} {:>16} {}'.format("Location Name", "Area", "Item", "Difficulty"))
        print('-'*92)
        for location in visitedLocations:
            if items.has_key(location['item']):
                itemName = items[location['item']]['name']
            else:
                itemName = 'The End'
            print('{:>50}: {:>12} {:>16} {}'.format(location['Name'], location['Area'], itemName, location['difficulty'][1]))

    if not enoughMajors(collectedItems, majorLocations) or not enoughMinors(collectedItems, minorLocations) or not canEndGame(collectedItems):
        # we have aborted
        difficulty = (-1, -1)
    else:
        # sum difficulty for all visited locations
        difficulty_sum = 0
        difficulty_max = 0
        for loc in visitedLocations:
            difficulty_sum = difficulty_sum + loc['difficulty'][1]
            difficulty_max = max(difficulty_max, loc['difficulty'][1])
        # we compute the number of '+' that we'll display next to the difficulty to take in
        # account the sum of the difficulties.
        if difficulty_sum > difficulty_max:
            difficulty = (difficulty_max, (difficulty_sum - difficulty_max) / (difficulty_max * 2))
        else:
            difficulty = (difficulty_max, 0)

    print("{}: remaining major: {}, remaining minor: {}, visited: {}".format(itemsPickup, len(majorLocations), len(minorLocations), len(visitedLocations)))

    return difficulty

items = {
    '0xeed7': {'name': 'ETank'},
    '0xeedb': {'name': 'Missile'},
    '0xeedf': {'name': 'Super'},
    '0xeee3': {'name': 'PowerBomb'},
    '0xeee7': {'name': 'Bomb'},
    '0xeeeb': {'name': 'Charge'},
    '0xeeef': {'name': 'Ice'},
    '0xeef3': {'name': 'HiJump'},
    '0xeef7': {'name': 'SpeedBooster'},
    '0xeefb': {'name': 'Wave'},
    '0xeeff': {'name': 'Spazer'},
    '0xef03': {'name': 'SpringBall'},
    '0xef07': {'name': 'Varia'},
    '0xef13': {'name': 'Plasma'},
    '0xef17': {'name': 'Grapple'},
    '0xef23': {'name': 'Morph'},
    '0xef27': {'name': 'Reserve'},
    '0xef0b': {'name': 'Gravity'},
    '0xef0f': {'name': 'XRayScope'},
    '0xef1b': {'name': 'SpaceJump'},
    '0xef1f': {'name': 'ScrewAttack'}
}


def getLocation(name):
    for loc in locations:
        if loc['Name'] == name:
            return loc
    return None


# generated with:
# sed -e "s+\([A-Z][a-z]*\) =+'\1' =+" -e 's+ =+:+' -e 's+: \([A-Z][a-z]*\);+: "\1",+' -e 's+";+",+' -e 's+\(0x[0-9A-D]*\);+\1,+' -e 's+fun items -> +lambda items: +' -e 's+};+},+' -e 's+^            ++' locations.fs > locations.py
locations = [
{
    'Area': "Crateria",
    'Name': "Energy Tank, Gauntlet",
    'Class': "Major",
    'Address': 0x78264,
    'Visibility': "Visible",
    # DONE: difficulty already handled in the canEnterAndLeaveGauntlet function
    'Available': lambda items: canEnterAndLeaveGauntlet(items)
},
{
    'Area': "Crateria",
    'Name': "Bomb",
    'Address': 0x78404,
    'Class': "Major",
    'Visibility': "Chozo",
    # DONE: need to morph to enter Alcatraz. red door at Flyway
    'Available': lambda items: wand(haveItem(items, 'Morph'), canOpenRedDoors(items))
},
{
    'Area': "Crateria",
    'Name': "Energy Tank, Terminator",
    'Class': "Major",
    'Address': 0x78432,
    'Visibility': "Visible",
    # DONE: rewrote condition. initial condition was good for the randomizer itself
    #       but not for difficulty estimation. We know that if no power bombs are
    #       found early, BT will give either Bomb, ScrewAttack or SpeedBooster,
    #       so we reflect that logic for the item immediately after Bomb
    # FIXME: that SpeedBooster check is if you had to do alcatraz...
    #        check if that implies a short charge?
    'Available': lambda items: wor(wand(knowsAlcatrazEscape, haveItem(items, 'SpeedBooster')), wand(knowsAlcatrazEscape, haveItem(items, 'ScrewAttack')), canDestroyBombWalls(items))

},
{
    'Area': "Brinstar",
    'Name': "Reserve Tank, Brinstar",
    'Class': "Major",
    'Address': 0x7852C,
    'Visibility': "Chozo",
    # DONE: break the bomb wall at left of Parlor and Alcatraz,
    #       open red door at Green Brinstar Main Shaft,
    #       mock ball for early retreval or speed booster
    'Available': lambda items: wand(wor(haveItem(items, 'SpeedBooster'), canDestroyBombWalls(items)), canOpenRedDoors(items), wor(wand(knowsMockball, haveItem(items, 'Morph')), haveItem(items, 'SpeedBooster')))
},
{
    'Area': "Brinstar",
    'Name': "Charge Beam",
    'Class': "Major",
    'Address': 0x78614,
    'Visibility': "Chozo",
    # DONE: open red door at Green Brinstar Main Shaft,
    #       break the bomb wall at left of Parlor and Alcatraz
    'Available': lambda items: wand(canOpenRedDoors(items), wor(canPassBombPassages(items), canUsePowerBombs(items)))
},
{
    'Area': "Brinstar",
    'Name': "Morphing Ball",
    'Class': "Major",
    'Address': 0x786DE,
    'Visibility': "Visible",
    # DONE: no difficulty
    'Available': lambda items: (True, 0)
},
{
    'Area': "Brinstar",
    'Name': "Energy Tank, Brinstar Ceiling",
    'Class': "Major",
    'Address': 0x7879E,
    'Visibility': "Hidden",
    # DONE: to get this major items the different technics are:
    #  -can fly (continuous bomb jump or space jump)
    #  -have the high jump boots
    #  -freeze the Reo to jump on it
    #  -do a damage boost with one of the two Geemers
    'Available': lambda items: wor(knowsCeilingDBoost, canFly(items), haveItem(items, 'HiJump'), haveItem(items, 'Ice'))
},
{
    'Area': "Brinstar",
    'Name': "Energy Tank, Etecoons",
    'Class': "Major",
    'Address': 0x787C2,
    'Visibility': "Visible",
    # DONE: no difficulty
    'Available': lambda items: canUsePowerBombs(items)
},
{
    'Area': "Brinstar",
    'Name': "Energy Tank, Waterway",
    'Class': "Major",
    'Address': 0x787FA,
    'Visibility': "Visible",
    # DONE: use knowsSimpleShortCharge
    'Available': lambda items: wand(canUsePowerBombs(items), canOpenRedDoors(items), haveItem(items, 'SpeedBooster'), wor(haveItem(items, 'Gravity'), knowsSimpleShortCharge))
},
{
    'Area': "Brinstar",
    'Name': "Energy Tank, Brinstar Gate",
    'Class': "Major",
    'Address': 0x78824,
    'Visibility': "Visible",
    # DONE: use knowsReverseGateGlitch
    'Available': lambda items: wand(canUsePowerBombs(items), wor(haveItem(items, 'Wave'), wand(haveItem(items, 'Super'), haveItem(items, 'HiJump'), knowsReverseGateGlitch)))
},
{
    'Area': "Brinstar",
    'Name': "X-Ray Scope",
    'Class': "Major",
    'Address': 0x78876,
    'Visibility': "Chozo",
    # original condition (easier to read, I have to put the lambda function on one line):
    #                Available = fun items ->canAccessRedBrinstar items && 
    #                                        canUsePowerBombs items &&
    #                                        (haveItem items Grapple ||
    #                                         haveItem items SpaceJump ||
    #                                         (haveItem items Varia && energyReserveCount items >= 4) ||
    #                                         (energyReserveCount items >= 6))
    'Available': lambda items: wand(canAccessRedBrinstar(items), canUsePowerBombs(items), wor(haveItem(items, 'Grapple'), haveItem(items, 'SpaceJump'), wand(haveItem(items, 'Varia'), energyReserveCountOk(items, 4), knowsXrayDboost), wand(energyReserveCountOk(items, 6), knowsXrayDboost)))
},
{
    'Area': "Brinstar",
    'Name': "Spazer",
    'Class': "Major",
    'Address': 0x7896E,
    'Visibility': "Chozo",
    # DONE: no difficulty
    'Available': lambda items: canAccessRedBrinstar(items)
},
{
    'Area': "Brinstar",
    'Name': "Energy Tank, Kraid",
    'Class': "Major",
    'Address': 0x7899C,
    'Visibility': "Hidden",
    # DONE: no difficulty
    'Available': lambda items: wand(canAccessKraid(items), enoughStuffsKraid(items))
},
{
    'Area': "Brinstar",
    'Name': "Varia Suit",
    'Class': "Major",
    'Address': 0x78ACA,
    'Visibility': "Chozo",
    # DONE: no difficulty
    'Available': lambda items: wand(canAccessKraid(items), enoughStuffsKraid(items))
},
{
    'Area': "Norfair",
    'Name': "Ice Beam",
    'Class': "Major",
    'Address': 0x78B24,
    'Visibility': "Chozo",
    # DONE: harder without varia
    'Available': lambda items: wand(canAccessKraid(items), wor(heatProof(items), energyReserveCountOkList(items, hellRuns['Ice'])), wor(wand(haveItem(items, 'Morph'), knowsMockball), haveItem(items, 'SpeedBooster'))) # FIXME : knowsEarlyKraid has nothing to do with this and is implied by canAccessKraid
},
{
    'Area': "Norfair",
    'Name': "Energy Tank, Crocomire",
    'Class': "Major",
    'Address': 0x78BA4,
    'Visibility': "Visible",
    # DONE: difficulty already set in canHellRun
    'Available': lambda items: canAccessCrocomire(items)
},
{
    'Area': "Norfair",
    'Name': "Hi-Jump Boots",
    'Class': "Major",
    'Address': 0x78BAC,
    'Visibility': "Chozo",
    # DONE: no difficulty
    'Available': lambda items: canAccessRedBrinstar(items)
},
{
    'Area': "Norfair",
    'Name': "Grapple Beam",
    'Class': "Major",
    'Address': 0x78C36,
    'Visibility': "Chozo",
    'Available': lambda items: wand(canAccessCrocomire(items), wor(canFly(items), wand(haveItem(items, 'Ice'), knowsClimbToGrappleWithIce), haveItem(items, 'SpeedBooster'), knowsGreenGateGlitch))
},
{
    'Area': "Norfair",
    'Name': "Reserve Tank, Norfair",
    'Class': "Major",
    'Address': 0x78C3E,
    'Visibility': "Chozo",
    'Available': lambda items: wand(canAccessHeatedNorfair(items), wor(canFly(items), haveItem(items, 'Grapple'), haveItem(items, 'HiJump', difficulty=hard)))
},
{
    'Area': "Norfair",
    'Name': "Speed Booster",
    'Class': "Major",
    'Address': 0x78C82,
    'Visibility': "Chozo",
    # DONE: difficulty already done in the function
    'Available': lambda items: canAccessHeatedNorfair(items)
},
{
    'Area': "Norfair",
    'Name': "Wave Beam",
    'Class': "Major",
    'Address': 0x78CCA,
    'Visibility': "Chozo",
    # DONE: this one is not easy without grapple beam nor space jump, with hijump medium wall jump is required
    # FLO : no need of high jump for this, just wall jumping
    'Available': lambda items: wand(canAccessHeatedNorfair(items), wor(haveItem(items, 'Grapple'), haveItem(items, 'SpaceJump'), (True, medium)))
},
{
    'Area': "LowerNorfair",
    'Name': "Energy Tank, Ridley",
    'Class': "Major",
    'Address': 0x79108,
    'Visibility': "Hidden",
    # DONE: already set in function
    'Available': lambda items: wand(canPassWorstRoom(items), enoughStuffsRidley(items))
},
{
    'Area': "LowerNorfair",
    'Name': "Screw Attack",
    'Class': "Major",
    'Address': 0x79110,
    'Visibility': "Chozo",
    # DONE: easy with green gate glitch
    'Available': lambda items: wand(canAccessLowerNorfair(items), wor(haveItem(items, 'SpaceJump'), knowsGreenGateGlitch))
},
{
    'Area': "LowerNorfair",
    'Name': "Energy Tank, Firefleas",
    'Class': "Major",
    'Address': 0x79184,
    'Visibility': "Visible",
    'Available': lambda items: canPassWorstRoom(items)
},
{
    'Area': "WreckedShip",
    'Name': "Reserve Tank, Wrecked Ship",
    'Class': "Major",
    'Address': 0x7C2E9,
    'Visibility': "Chozo",
    # DONE: easy
    'Available': lambda items: wand(canAccessWs(items), enoughStuffsPhantoon(items), haveItem(items, 'SpeedBooster'), wor(haveItem(items, 'Varia'), energyReserveCountOk(items, 1)))
},
{
    'Area': "WreckedShip",
    'Name': "Energy Tank, Wrecked Ship",
    'Class': "Major",
    'Address': 0x7C337,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessWs(items), enoughStuffsPhantoon(items), wor(wor(haveItem(items, 'Bomb'), haveItem(items, 'PowerBomb')), knowsSpongeBathBombJump, wand(haveItem(items, 'HiJump'), knowsSpongeBathHiJump), wor(haveItem(items, 'SpaceJump', difficulty=easy), wand(haveItem(items, 'SpeedBooster'), knowsSpongeBathSpeed), wand(haveItem(items, 'SpringBall'), knowsSpringBallJump))))
# test in the randomizer (easier to read)
#                Available = fun items -> canAccessWs items &&
#                                            (haveItem items Bomb ||
#                                             haveItem items PowerBomb ||
#                                             haveItem items HiJump ||
#                                             haveItem items SpaceJump ||
#                                             haveItem items SpeedBooster ||
#                                             haveItem items SpringBall);
},
{
    'Area': "WreckedShip",
    'Name': "Right Super, Wrecked Ship",
    'Class': "Major",
    'Address': 0x7C365,
    'Visibility': "Visible",
    # DONE: easy once WS is accessible
    'Available': lambda items: wand(canAccessWs(items), enoughStuffsPhantoon(items))
},
{
    'Area': "WreckedShip",
    'Name': "Gravity Suit",
    'Class': "Major",
    'Address': 0x7C36D,
    'Visibility': "Chozo",
    # DONE: easy
    'Available': lambda items: wand(canAccessWs(items), enoughStuffsPhantoon(items), wor(haveItem(items, 'Varia'), energyReserveCountOk(items, 1)))
},
{
    'Area': "Maridia",
    'Name': "Energy Tank, Mama turtle",
    'Class': "Major",
    'Address': 0x7C47D,
    'Visibility': "Visible",
    # DONE: difficulty already handled in canAccessOuterMaridia
    # to acces the ETank in higher part of the room:
    #  -use grapple to attach to the block
    #  -use speedbooster ??
    #  FIXME: is SpeedBooster possible without gravity in this room ? is it a simple short or short charge ?
    #  -can fly (space jump or infinite bomb jump)
    #  FIXME: is it possible to infinite bomb jump from the mama turtle when it's up ?
    'Available': lambda items: wand(canAccessOuterMaridia(items), wor(canFly(items), haveItem(items, 'SpeedBooster'), haveItem(items, 'Grapple')))
},
{
    'Area': "Maridia",
    'Name': "Plasma Beam",
    'Class': "Major",
    'Address': 0x7C559,
    'Visibility': "Chozo",
    # DONE: to leave the Plasma Beam room you have to kill the space pirates and return to the door
    # to unlock the door:
    #  -can access draygon room to kill him
    #  -have enough stuff to kill him
    # to kill the space pirates:
    #  -do short charges with speedbooster
    #  -do beam charges with spin jump attacks
    #  -have screw attack
    #  -have plasma beam
    # to go back to the door:
    #  -have high jump boots
    #  -can fly (space jump or infinite bomb jump)
    #  -use short charge with speedbooster
    'Available': lambda items: wand(canDefeatDraygon(items), enoughStuffsDraygon(items), wor(wand(haveItem(items, 'SpeedBooster'), knowsShortCharge, knowsKillPlasmaPiratesWithSpark), wand(haveItem(items, 'Charge'), knowsKillPlasmaPiratesWithCharge), haveItem(items, 'ScrewAttack', difficulty=easy), haveItem(items, 'Plasma', difficulty=easy)), wor(canFly(items), wand(haveItem(items, 'HiJump'), knowsExitPlasmaRoomHiJump), wand(haveItem(items, 'SpeedBooster'), knowsShortCharge)))
},
{
    'Area': "Maridia",
    'Name': "Reserve Tank, Maridia",
    'Class': "Major",
    'Address': 0x7C5E3,
    'Visibility': "Chozo",
    # DONE: this item can be taken without gravity, but it's super hard because of the quick sands...
    'Available': lambda items: wand(canAccessOuterMaridia(items), wor(haveItem(items, 'Gravity'), wand(canDoSuitlessMaridia(items), knowsSuitlessSandpit)))
},
{
    'Area': "Maridia",
    'Name': "Spring Ball",
    'Class': "Major",
    'Address': 0x7C6E5,
    'Visibility': "Chozo",
    # DONE: handle puyo clip and diagonal bomb jump
    # to access the spring ball you can either:
    #  -use the puyo clip with ice
    #  -use the grapple to destroy the block and then:
    #    -use high boots jump
    #    -fly (with space jump or diagonal bomb jump
    'Available': lambda items: wand(canAccessInnerMaridia(items), wor(wand(haveItem(items, 'Ice'), knowsPuyoClip), wand(haveItem(items, 'Grapple'), wor(canFlyDiagonally(items), haveItem(items, 'HiJump')))))
},
{
    'Area': "Maridia",
    'Name': "Energy Tank, Botwoon",
    'Class': "Major",
    'Address': 0x7C755,
    'Visibility': "Visible",
    # DONE: difficulty already handled in the functions
    'Available': lambda items: canDefeatBotwoon(items)
},
{
    'Area': "Maridia",
    'Name': "Space Jump",
    'Class': "Major",
    'Address': 0x7C7A7,
    'Visibility': "Chozo",
    # DONE: difficulty already handled in the function,
    # we need to have access to the boss and enough stuff to kill him
    'Available': lambda items: wand(canDefeatDraygon(items), enoughStuffsDraygon(items))
},
{
    'Area': "Crateria",
    'Name': "Power Bomb (Crateria surface)",
    'Class': "Minor",
    'Address': 0x781CC,
    'Visibility': "Visible",
    'Available': lambda items: wand(canUsePowerBombs(items), wor(haveItem(items, 'SpeedBooster'), canFly(items)))
},
{
    'Area': "Crateria",
    'Name': "Missile (outside Wrecked Ship bottom)",
    'Class': "Minor",
    'Address': 0x781E8,
    'Visibility': "Visible",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "Crateria",
    'Name': "Missile (outside Wrecked Ship top)",
    'Class': "Minor",
    'Address': 0x781EE,
    'Visibility': "Hidden",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "Crateria",
    'Name': "Missile (outside Wrecked Ship middle)",
    'Class': "Minor",
    'Address': 0x781F4,
    'Visibility': "Visible",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "Crateria",
    'Name': "Missile (Crateria moat)",
    'Class': "Minor",
    'Address': 0x78248,
    'Visibility': "Visible",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "Crateria",
    'Name': "Missile (Crateria bottom)",
    'Class': "Minor",
    'Address': 0x783EE,
    'Visibility': "Visible",
    'Available': lambda items: canDestroyBombWalls(items)
},
{
    'Area': "Crateria",
    'Name': "Missile (Crateria gauntlet right)",
    'Class': "Minor",
    'Address': 0x78464,
    'Visibility': "Visible",
    'Available': lambda items: wand(canEnterAndLeaveGauntlet(items), canPassBombPassages(items))
},
{
    'Area': "Crateria",
    'Name': "Missile (Crateria gauntlet left)",
    'Class': "Minor",
    'Address': 0x7846A,
    'Visibility': "Visible",
    'Available': lambda items: wand(canEnterAndLeaveGauntlet(items), canPassBombPassages(items))
},
{
    'Area': "Crateria",
    'Name': "Super Missile (Crateria)",
    'Class': "Minor",
    'Address': 0x78478,
    'Visibility': "Visible",
    'Available': lambda items: wand(canUsePowerBombs(items), haveItem(items, 'SpeedBooster'), wor(wand(haveItem(items, 'Ice'), (True, easy)), wand(haveItem(items, 'ETank'), haveItem(items, 'Varia'), haveItem(items, 'Gravity'), difficulty=hardcore))) # hardcore dboost...
},
{
    'Area': "Crateria",
    'Name': "Missile (Crateria middle)",
    'Class': "Minor",
    'Address': 0x78486,
    'Visibility': "Visible",
    'Available': lambda items: canPassBombPassages(items)
},
{
    'Area': "Brinstar",
    'Name': "Power Bomb (green Brinstar bottom)",
    'Class': "Minor",
    'Address': 0x784AC,
    'Visibility': "Chozo",
    'Available': lambda items: canUsePowerBombs(items)
},
{
    'Area': "Brinstar",
    'Name': "Super Missile (pink Brinstar)",
    'Class': "Minor",
    'Address': 0x784E4,
    'Visibility': "Chozo",
    'Available': lambda items: wand(canPassBombPassages(items), haveItem(items, 'Super'))
},
{
    'Area': "Brinstar",
    'Name': "Missile (green Brinstar below super missile)",
    'Class': "Minor",
    'Address': 0x78518,
    'Visibility': "Visible",
    'Available': lambda items: wand(canPassBombPassages(items), canOpenRedDoors(items))
},
{
    'Area': "Brinstar",
    'Name': "Super Missile (green Brinstar top)",
    'Class': "Minor",
    'Address': 0x7851E,
    'Visibility': "Visible",
    'Available': lambda items: wand(wor(haveItem(items, 'SpeedBooster'), canDestroyBombWalls(items)), canOpenRedDoors(items), wor(haveItem(items, 'Morph'), haveItem(items, 'SpeedBooster')))
},
{
    'Area': "Brinstar",
    'Name': "Missile (green Brinstar behind missile)",
    'Class': "Minor",
    'Address': 0x78532,
    'Visibility': "Hidden",
    'Available': lambda items: wand(canPassBombPassages(items), canOpenRedDoors(items))
},
{
    'Area': "Brinstar",
    'Name': "Missile (green Brinstar behind reserve tank)",
    'Class': "Minor",
    'Address': 0x78538,
    'Visibility': "Visible",
    'Available': lambda items: wand(canDestroyBombWalls(items), canOpenRedDoors(items), haveItem(items, 'Morph'))
},
{
    'Area': "Brinstar",
    'Name': "Missile (pink Brinstar top)",
    'Class': "Minor",
    'Address': 0x78608,
    'Visibility': "Visible",
    'Available': lambda items: wor(wand(canDestroyBombWalls(items), canOpenRedDoors(items)), canUsePowerBombs(items))
},
{
    'Area': "Brinstar",
    'Name': "Missile (pink Brinstar bottom)",
    'Class': "Minor",
    'Address': 0x7860E,
    'Visibility': "Visible",
    'Available': lambda items: wor(wand(canDestroyBombWalls(items), canOpenRedDoors(items)), canUsePowerBombs(items))
},
{
    'Area': "Brinstar",
    'Name': "Power Bomb (pink Brinstar)",
    'Class': "Minor",
    'Address': 0x7865C,
    'Visibility': "Visible",
    'Available': lambda items: wand(canUsePowerBombs(items), haveItem(items, 'Super'))
},
{
    'Area': "Brinstar",
    'Name': "Missile (green Brinstar pipe)",
    'Class': "Minor",
    'Address': 0x78676,
    'Visibility': "Visible",
    'Available': lambda items: wor(wand(canPassBombPassages(items), canOpenGreenDoors(items)), canUsePowerBombs(items))
},
{
    'Area': "Brinstar",
    'Name': "Power Bomb (blue Brinstar)",
    'Class': "Minor",
    'Address': 0x7874C,
    'Visibility': "Visible",
    'Available': lambda items: canUsePowerBombs(items)
},
{
    'Area': "Brinstar",
    'Name': "Missile (blue Brinstar middle)",
    'Address': 0x78798,
    'Class': "Minor",
    'Visibility': "Visible",
    'Available': lambda items: haveItem(items, 'Morph')
},
{
    'Area': "Brinstar",
    'Name': "Super Missile (green Brinstar bottom)",
    'Class': "Minor",
    'Address': 0x787D0,
    'Visibility': "Visible",
    'Available': lambda items: wand(canUsePowerBombs(items), canOpenGreenDoors(items))
},
{
    'Area': "Brinstar",
    'Name': "Missile (blue Brinstar bottom)",
    'Class': "Minor",
    'Address': 0x78802,
    'Visibility': "Chozo",
    'Available': lambda items: haveItem(items, 'Morph')
},
{
    'Area': "Brinstar",
    'Name': "Missile (blue Brinstar top)",
    'Class': "Minor",
    'Address': 0x78836,
    'Visibility': "Visible",
    'Available': lambda items: canUsePowerBombs(items)
},
{
    'Area': "Brinstar",
    'Name': "Missile (blue Brinstar behind missile)",
    'Class': "Minor",
    'Address': 0x7883C,
    'Visibility': "Hidden",
    'Available': lambda items: canUsePowerBombs(items)
},
{
    'Area': "Brinstar",
    'Name': "Power Bomb (red Brinstar sidehopper room)",
    'Class': "Minor",
    'Address': 0x788CA,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessRedBrinstar(items), canUsePowerBombs(items))
},
{
    'Area': "Brinstar",
    'Name': "Power Bomb (red Brinstar spike room)",
    'Class': "Minor",
    'Address': 0x7890E,
    'Visibility': "Chozo",
    'Available': lambda items: wand(canAccessRedBrinstar(items), canUsePowerBombs(items))
},
{
    'Area': "Brinstar",
    'Name': "Missile (red Brinstar spike room)",
    'Class': "Minor",
    'Address': 0x78914,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessRedBrinstar(items), canUsePowerBombs(items))
},
{
    'Area': "Brinstar",
    'Name': "Missile (Kraid)",
    'Class': "Minor",
    'Address': 0x789EC,
    'Visibility': "Hidden",
    'Available': lambda items: wand(canAccessKraid(items), canUsePowerBombs(items))
},
{
    'Area': "Norfair",
    'Name': "Missile (lava room)",
    'Class': "Minor",
    'Address': 0x78AE4,
    'Visibility': "Hidden",
    'Available': lambda items: canAccessHeatedNorfair(items)
},
{
    'Area': "Norfair",
    'Name': "Missile (below Ice Beam)",
    'Class': "Minor",
    'Address': 0x78B46,
    'Visibility': "Hidden",
    'Available': lambda items: wand(canAccessKraid(items), canUsePowerBombs(items), canHellRun(items))
},
{
    'Area': "Norfair",
    'Name': "Missile (above Crocomire)",
    'Class': "Minor",
    'Address': 0x78BC0,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessCrocomire(items), wor(canFly(items), haveItem(items, 'Grapple'), wand(haveItem(items, 'HiJump'), haveItem(items, 'SpeedBooster'))))
},
{
    'Area': "Norfair",
    'Name': "Missile (Hi-Jump Boots)",
    'Class': "Minor",
    'Address': 0x78BE6,
    'Visibility': "Visible",
    'Available': lambda items: canAccessRedBrinstar(items)
},
{
    'Area': "Norfair",
    'Name': "Energy Tank (Hi-Jump Boots)",
    'Class': "Minor",
    'Address': 0x78BEC,
    'Visibility': "Visible",
    'Available': lambda items: canAccessRedBrinstar(items)
},
{
    'Area': "Norfair",
    'Name': "Power Bomb (Crocomire)",
    'Class': "Minor",
    'Address': 0x78C04,
    'Visibility': "Visible",
    'Available': lambda items: canAccessCrocomire(items)
},
{
    'Area': "Norfair",
    'Name': "Missile (below Crocomire)",
    'Class': "Minor",
    'Address': 0x78C14,
    'Visibility': "Visible",
    'Available': lambda items: canAccessCrocomire(items)
},
{
    'Area': "Norfair",
    'Name': "Missile (Grapple Beam)",
    'Class': "Minor",
    'Address': 0x78C2A,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessCrocomire(items), wor(canFly(items), haveItem(items, 'Grapple'), haveItem(items, 'SpeedBooster')))
},
{
    'Area': "Norfair",
    'Name': "Missile (Norfair Reserve Tank)",
    'Class': "Minor",
    'Address': 0x78C44,
    'Visibility': "Hidden",
    'Available': lambda items: wand(canAccessHeatedNorfair(items), wor(canFly(items), haveItem(items, 'Grapple'), haveItem(items, 'HiJump')))
},
{
    'Area': "Norfair",
    'Name': "Missile (bubble Norfair green door)",
    'Class': "Minor",
    'Address': 0x78C52,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessHeatedNorfair(items), wor(canFly(items), haveItem(items, 'Grapple'), haveItem(items, 'HiJump')))
},
{
    'Area': "Norfair",
    'Name': "Missile (bubble Norfair)",
    'Class': "Minor",
    'Address': 0x78C66,
    'Visibility': "Visible",
    'Available': lambda items: canAccessHeatedNorfair(items)
},
{
    'Area': "Norfair",
    'Name': "Missile (Speed Booster)",
    'Class': "Minor",
    'Address': 0x78C74,
    'Visibility': "Hidden",
    'Available': lambda items: canAccessHeatedNorfair(items)
},
{
    'Area': "Norfair",
    'Name': "Missile (Wave Beam)",
    'Class': "Minor",
    'Address': 0x78CBC,
    'Visibility': "Visible",
    'Available': lambda items: canAccessHeatedNorfair(items)
},
{
    'Area': "LowerNorfair",
    'Name': "Missile (Gold Torizo)",
    'Class': "Minor",
    'Address': 0x78E6E,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessLowerNorfair(items), haveItem(items, 'SpaceJump'))
},
{
    'Area': "LowerNorfair",
    'Name': "Super Missile (Gold Torizo)",
    'Class': "Minor",
    'Address': 0x78E74,
    'Visibility': "Hidden",
    'Available': lambda items: canAccessLowerNorfair(items)
},
{
    'Area': "LowerNorfair",
    'Name': "Missile (Mickey Mouse room)",
    'Class': "Minor",
    'Address': 0x78F30,
    'Visibility': "Visible",
    'Available': lambda items: canPassWorstRoom(items)
},
{
    'Area': "LowerNorfair",
    'Name': "Missile (lower Norfair above fire flea room)",
    'Class': "Minor",
    'Address': 0x78FCA,
    'Visibility': "Visible",
    'Available': lambda items: canPassWorstRoom(items)
},
{
    'Area': "LowerNorfair",
    'Name': "Power Bomb (lower Norfair above fire flea room)",
    'Class': "Minor",
    'Address': 0x78FD2,
    'Visibility': "Visible",
    'Available': lambda items: canPassWorstRoom(items)
},
{
    'Area': "LowerNorfair",
    'Name': "Power Bomb (Power Bombs of shame)",
    'Class': "Minor",
    'Address': 0x790C0,
    'Visibility': "Visible",
    'Available': lambda items: canPassWorstRoom(items)
},
{
    'Area': "LowerNorfair",
    'Name': "Missile (lower Norfair near Wave Beam)",
    'Class': "Minor",
    'Address': 0x79100,
    'Visibility': "Visible",
    'Available': lambda items: canPassWorstRoom(items)
},
{
    'Area': "WreckedShip",
    'Name': "Missile (Wrecked Ship middle)",
    'Class': "Minor",
    'Address': 0x7C265,
    'Visibility': "Visible",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "WreckedShip",
    'Name': "Missile (Gravity Suit)",
    'Class': "Minor",
    'Address': 0x7C2EF,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessWs(items), wor(haveItem(items, 'Varia'), energyReserveCountOk(items, 1)))
},
{
    'Area': "WreckedShip",
    'Name': "Missile (Wrecked Ship top)",
    'Class': "Minor",
    'Address': 0x7C319,
    'Visibility': "Visible",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "WreckedShip",
    'Name': "Super Missile (Wrecked Ship left)",
    'Class': "Minor",
    'Address': 0x7C357,
    'Visibility': "Visible",
    'Available': lambda items: canAccessWs(items)
},
{
    'Area': "Maridia",
    'Name': "Missile (green Maridia shinespark)",
    'Class': "Minor",
    'Address': 0x7C437,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessRedBrinstar(items), canUsePowerBombs(items), haveItem(items, 'Gravity'), haveItem(items, 'SpeedBooster'))
},
{
    'Area': "Maridia",
    'Name': "Super Missile (green Maridia)",
    'Class': "Minor",
    'Address': 0x7C43D,
    'Visibility': "Visible",
    'Available': lambda items: canAccessOuterMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Missile (green Maridia tatori)",
    'Class': "Minor",
    'Address': 0x7C483,
    'Visibility': "Hidden",
    'Available': lambda items: canAccessOuterMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Super Missile (yellow Maridia)",
    'Class': "Minor",
    'Address': 0x7C4AF,
    'Visibility': "Visible",
    'Available': lambda items: canAccessInnerMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Missile (yellow Maridia super missile)",
    'Class': "Minor",
    'Address': 0x7C4B5,
    'Visibility': "Visible",
    'Available': lambda items: canAccessInnerMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Missile (yellow Maridia false wall)",
    'Class': "Minor",
    'Address': 0x7C533,
    'Visibility': "Visible",
    'Available': lambda items: canAccessInnerMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Missile (left Maridia sand pit room)",
    'Class': "Minor",
    'Address': 0x7C5DD,
    'Visibility': "Visible",
    'Available': lambda items: canAccessInnerMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Missile (right Maridia sand pit room)",
    'Class': "Minor",
    'Address': 0x7C5EB,
    'Visibility': "Visible",
    'Available': lambda items: canAccessInnerMaridia(items)
},
{
    'Area': "Maridia",
    'Name': "Power Bomb (right Maridia sand pit room)",
    'Class': "Minor",
    'Address': 0x7C5F1,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessOuterMaridia(items), haveItem(items, 'Gravity'))
},
{
    'Area': "Maridia",
    'Name': "Missile (pink Maridia)",
    'Address': 0x7C603,
    'Class': "Minor",
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessOuterMaridia(items), haveItem(items, 'Gravity'))
},
{
    'Area': "Maridia",
    'Name': "Super Missile (pink Maridia)",
    'Class': "Minor",
    'Address': 0x7C609,
    'Visibility': "Visible",
    'Available': lambda items: wand(canAccessOuterMaridia(items), haveItem(items, 'Gravity'))
},
{
    'Area': "Maridia",
    'Name': "Missile (Draygon)",
    'Class': "Minor",
    'Address': 0x7C74D,
    'Visibility': "Hidden",
    'Available': lambda items: canDefeatBotwoon(items)
}
]

if len(sys.argv) != 2:
    print("missing param: rom file")
    sys.exit(0)

romName = sys.argv[1]
print("romName=" + romName)

romFile = open(romName, "r")

for location in locations:
    location["item"] = getItem(romFile, location["Address"], location["Visibility"])
    #print('{:>50}: {:>16}'.format(location["Name"], items[location["item"]]['name']))

romFile.close()

difficulty = getDifficulty(locations)

if difficulty[0] >= 0:
    if difficulty[0] >= easy and difficulty[0] < medium:
        difficultyText = 'easy'
    elif difficulty[0] >= medium and difficulty[0] < hard:
        difficultyText = 'medium'
    elif difficulty[0] >= hard and difficulty[0] < harder:
        difficultyText = 'hard'
    elif difficulty[0] >= harder and difficulty[0] < hardcore:
        difficultyText = 'very hard'
    elif difficulty[0] >= hardcore and difficulty[0] < mania:
        difficultyText = 'hardcore'
    else:
        difficultyText = 'mania'

    print("Estimated difficulty for items pickup {}: {}".format(itemsPickup, difficultyText))
else:
    print("Aborted run, can't finish the game with the given prerequisites")
