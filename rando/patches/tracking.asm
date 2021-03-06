// compile with xkas-plus

arch snes.cpu
lorom

// Addresses to helper functions for stat tracking
define inc_stat $dfd810         // Inc stat, stat id in A
define dec_stat $dfd840         // Dec stat, stat id in A
define store_stat $dfd880       // Store stat, value in A, stat id in X
define load_stat $dfd8b0        // Load stat, stat id in A, value returned in A
define save_last_stats $dfd820  // save stats to "last stats" area in SRAM

// RTA Timer (timer 1 is frames, and timer 2 is number of times frames rolled over)
define timer1 $05b8
define timer2 $05ba

// beggining of stats region
define stats $7ffc00

// Temp variables (define here to make sure they're not reused, make sure they're 2 bytes apart)
// These variables are cleared to 0x00 on hard and soft reset
define door_timer_tmp $7fff00
define door_adjust_tmp $7fff02

define add_time_tmp $7fff04

define region_timer_tmp $7fff06
define region_tmp $7fff08

define pause_timer_idx  #$ff0a
define pause_timer_lo $7fff0a
define pause_timer_hi $7fff0c

define add_time_32_tmp_lo $7fff0e
define add_time_32_tmp_hi $7fff1a

// -------------------------------
// HIJACKS
// -------------------------------

// Samus hit a door block (Gamestate change to $09 just before hitting $0a)
org $82e176
    jml door_entered

// Samus gains control back after door (Gamestate change back to $08 after door transition)
org $82e764
    jml door_exited

// Door starts adjusting
org $82e309
    jml door_adjust_start

// Door stops adjusting
org $82e34c
    jml door_adjust_stop

// samus is dead
org $82DCD8
    jsl death
    nop
    nop

// timer is up (equivalent to death)
org $828423
    jsl time_up
    nop
    nop

// Firing uncharged beam
org $90b911
    jml uncharged_beam
org $90b92a
    jml uncharged_beam
org $90bd5f
    jml hyper_shot

// Firing charged beam
org $90b9a1
    jml charged_beam

// Firing SBAs
org $90ccde
    jmp fire_sba_local

//Missiles/supers fired
org $90beb7
    jml missiles_fired

//Bombs/PBs laid
org $90c107
    jml bombs_laid

org $90f800
fire_sba_local:
    jml fire_sba


// screen finished fading out
org $828cea
    jmp pausing_local

// screen starts fading in
org $82939c
    jmp resuming_local

org $82fc00
pausing_local:
    jml pausing
resuming_local:
    jml resuming

// -------------------------------
// CODE (using bank A1 free space)
// -------------------------------
org $a1ec00
// Helper function to add a time delta, X = stat to add to, A = value to check against
// This uses 4-bytes for each time delta
add_time:
    sta {add_time_tmp}
    lda {timer1}
    sec
    sbc {add_time_tmp}
    sta {add_time_tmp}
    txa
    jsl {load_stat}
    clc
    adc {add_time_tmp}
    bcc +
    jsl {store_stat}    // If carry set, increase the high bits
    inx
    txa
    jsl {inc_stat}
+
    jsl {store_stat}
    rts

// same as above, using 32bits date for couting long times (> 65535 frames, ~18min)
// X = offset in bank 7F for 32-bit tmp var, Y = stat to add to
add_time_32:
    // first, do the 32-bit subtraction
    lda $7f0000,x
    sta {add_time_32_tmp_lo}
    inx
    inx
    lda $7f0000,x
    sta {add_time_32_tmp_hi}
    sec				// set carry for borrow purpose
    lda {timer1}
    sbc {add_time_32_tmp_lo}	// perform subtraction on the LSBs
    sta {add_time_32_tmp_lo}
    lda {timer2}			// do the same for the MSBs, with carry
    sbc {add_time_32_tmp_hi}
    sta {add_time_32_tmp_hi}
    // add to current 32 bit stat value (don't use load_stat/store_stat for shorter code)
    tya
    asl
    tax
    lda {stats},x
    clc				// clear carry
    adc {add_time_32_tmp_lo}	// add LSBs
    sta {stats},x
    inx
    inx
    lda {stats},x
    adc {add_time_32_tmp_hi}	// add the MSBs using carry
    sta {stats},x
    rts

// Samus hit a door block (Gamestate change to $09 just before hitting $0a)
door_entered:
    // save last stats to resist power cycle
    jsl {save_last_stats}
    // Number of door transitions
    lda #$0002
    jsl {inc_stat}
    // Save RTA time to temp variable
    lda {timer1}
    sta {door_timer_tmp}
    // Run hijacked code and return
    plp
    inc $0998
    jml $82e1b7

update_region_time:
    // Store time spent in last room/area unless region_tmp is 0
    lda {region_tmp}
    beq +
    tax
    lda {region_timer_tmp}
    jsr add_time
+
    rts
store_region_time:
    // Store the current frame and the current region to temp variables
    lda {timer1}
    sta {region_timer_tmp}
    rts

// Samus gains control back after door (Gamestate change back to $08 after door transition)
door_exited:
    // Increment saved value with time spent in door transition
    lda {door_timer_tmp}
    ldx #$0003
    jsr add_time
    // update time spent in region since last store_region_time call,
    jsr update_region_time
    jsr store_region_time
    // Store (region*2) + 7 to region_tmp (This uses stat id 7-18 for region timers)
    lda $7e079f
    asl
    clc
    adc #$0007
    sta {region_tmp}

    // Run hijacked code and return
    lda #$0008
    sta $0998
    jml $82e76a

// Door adjust start
door_adjust_start:
    lda {timer1}
    sta {door_adjust_tmp} // Save RTA time to temp variable

    // Run hijacked code and return
    lda #$e310
    sta $099c
    jml $82e30f

// Door adjust stop
door_adjust_stop:
    lda {door_adjust_tmp}
    inc // Add extra frame to time delta so that perfect doors counts as 0
    ldx #$0005
    jsr add_time

    // Run hijacked code and return
    lda #$e353
    sta $099c
    jml $82e352

// samus is dead
death:
    lda #$001f
    jsl {inc_stat}
    jsl {save_last_stats}
    // hijacked code
    stz $18aa
    inc $0998
    rtl

// timer is up (equivalent to death)
time_up:
    lda #$001f
    jsl {inc_stat}
    jsl {save_last_stats}
    // hijacked code
    lda #$0024
    sta $0998
    rtl

// uncharged Beam Fire
uncharged_beam:
    sta $0ccc // execute first part of hijacked code, to freely use A

    lda #$0013
    jsl {inc_stat}
    // do the vanilla check, done in both auto and normal fire
    pla
    bit #$0001
    bne +
    // jump back to common branches for auto and normal fire
    jml $90b933
+
    jml $90b94c

hyper_shot:
    sta $0cd0 // execute first part of hijacked code, to freely use A

    lda #$0013
    jsl {inc_stat}

    plp // execute last instr of hijacked code
    jml $90bd63 // return

// Charged Beam Fire
charged_beam:
    lda #$0014
    jsl {inc_stat}
    // Run hijacked code and return
    LDX #$0000
    LDA $0c2c, x
    JML $90b9a7

// Firing SBAs : hijack the point where new qty of PBs is stored
fire_sba:
    // check if SBA routine actually changed PB count: means valid beam combo selected
    cmp $09ce
    beq .end
    pha
    lda #$0015
    jsl {inc_stat}
    pla
    // Run hijacked code and return
.end:
    sta $09ce
    jml $90cce1

//MissilesSupers used
missiles_fired:
    lda $09d2
    cmp #$0002
    beq .super
    dec $09c6
    lda #$0016
    jsl {inc_stat}
    bra .end
.super:
    dec $09ca
    lda #$0017
    jsl {inc_stat}
.end:
    jml $90bec7

//bombs/PBs laid
bombs_laid:
    lda $09d2			// HUD sleection index
    cmp #$0003
    beq .power_bomb
    lda #$001a
    bra .end
.power_bomb:
    lda #$0018
.end:
    jsl {inc_stat}
    //run hijacked code and return
    lda $0cd2
    inc
    jml $90c10b

// stopped fading out, game state about to change to 0Dh
pausing:
    // save last stats to resist power cycle
    jsl {save_last_stats}
    // Save RTA time to temp variable
    lda {timer1}
    sta {pause_timer_lo}
    lda {timer2}
    sta {pause_timer_hi}
    // don't count time spent in pause in region counters
    jsr update_region_time
    // run hijacked code and return
    inc $0998
    jml $828ced

// start fading in, game state about to change to 12h
resuming:
    // add time spent in pause to stat at 27-28 spot
    phy // XXX don't know whether Y is actually used in vanilla code, save it for safety
    ldy #$001b
    ldx {pause_timer_idx}
    jsr add_time_32
    ply
    // don't count  time spent in pause in region counters
    jsr store_region_time
    // save last stats to resist power cycle
    jsl {save_last_stats}
    // run hijacked code and return
    inc $0998
    jml $82939f

warnpc $a1efff
