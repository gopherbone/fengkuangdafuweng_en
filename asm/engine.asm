; English text engine for Feng Kuang Da Fu Weng (GBC).
; Hooks the original renderer's byte fetch at $0A43. A string whose first byte is $F6 is a redirect:
; F6 lo hi = index into the English string table (bank EN_TBL_BANK, 4 bytes/entry: ptr lo, ptr hi, bank, flags).
; English streams are ASCII ($20-$7E) + the original control codes ($E0-$FF), rendered with a proportional
; font into the same column-major 8x16 tile strip the original 16x16 renderer uses.

INCLUDE "defs.inc"

; ---------------------------------------------------------------- hooks in the original code
SECTION "hook_0a3b", ROM0[$0A3B]
    jp EnTop                ; was: ld a,[$C0DE]  (3 bytes)

SECTION "hook_0a43", ROM0[$0A43]
    jp EnHook               ; was: ld a,[hl+] / cp $FF  (3 bytes); original continues at $0A46

; bank $14 number-field routine (HUD cash, money popups, events): replaced by an English dollar field
SECTION "hook_14_5914", ROMX[$5914], BANK[$14]
    jp NumField             ; DE = 7-digit buffer (entered from $5907/$590C/$5911)
SECTION "hook_14_58d3", ROMX[$58D3], BANK[$14]
    jp NumFieldDebt         ; debt variant: 6 digits at $C222

; the money popup's 萬 glyph (copied after the number field): blank, the field shows full dollars
SECTION "blank_14_40ef", ROMX[$40EF], BANK[$14]
    ds 32, 0

; ---------------------------------------------------------------- engine (free ROM0 space)
SECTION "en_engine", ROM0[$3000]

; Top-level entry from $0A3B: mark that the next $0A43 entry starts/resumes a top-level string.
EnTop::
    ld a, 1
    ld [EN_TOP], a
    ld a, [$C0DE]
    jp $0A3E

; Every byte fetch of the original renderer comes here with HL = string pointer.
EnHook::
    ld a, h
    cp HIGH(EN_STUB)
    jr nz, .notStub
    ld a, l
    and $F0
    cp LOW(EN_STUB)
    jp z, EnResume
.notStub:
    ld a, [hl]
    cp $F6
    jr z, EnStart
    cp $F7
    jr z, EnStartInline
    ld a, [EN_TOP]
    and a
    jr z, .orig
    xor a
    ld [EN_FLAGS], a        ; a new top-level game string: no English stream is running
    ld [EN_DEPTH], a
.orig:
    xor a
    ld [EN_TOP], a
    ld [EN_INSERT], a
    ld a, [hl+]             ; original behaviour
    cp $FF
    jp $0A46

; ---- F7 + ASCII ... FD : inline English (e.g. names typed on the keyboard, stored in RAM)
EnStartInline::
    inc hl
    ld a, l
    ld [EN_TMP], a
    ld a, h
    ld [EN_TMP+1], a
    ld a, [$4000]
    ld [EN_CBANK], a
    ld b, a                 ; read from the caller's bank (RAM ignores the bank)
    ld c, 0                 ; flags
    jr EnBegin

; ---- F6 lo hi : redirect to English string table entry
EnStart::
    inc hl
    ld e, [hl]
    inc hl
    ld d, [hl]
    ld a, [$4000]
    ld [EN_CBANK], a
    ; DE = index -> table entry
    ld a, EN_TBL_BANK
    ld [rROMB], a
    ld h, d
    ld l, e
    add hl, hl
    add hl, hl
    ld bc, $4001
    add hl, bc
    ld a, [hl+]
    ld [EN_TMP], a
    ld a, [hl+]
    ld [EN_TMP+1], a
    ld a, [hl+]
    ld b, a                 ; data bank
    ld c, [hl]              ; flags
    ld a, [EN_CBANK]
    ld [rROMB], a
    ; fall through

; B = data bank, C = flags, EN_TMP = data pointer
EnBegin:
    ld a, [EN_INSERT]
    and a
    jr z, .top
    xor a
    ld [EN_INSERT], a
    ld a, [EN_FLAGS]
    bit FLAG_ACTIVE, a
    jr z, .top
    ; nested (name/word insert inside an English string): push outer stream
    ld a, [EN_PTR]
    ld [EN_SAVE], a
    ld a, [EN_PTR+1]
    ld [EN_SAVE+1], a
    ld a, [EN_BANK]
    ld [EN_SAVE+2], a
    ld a, [EN_FLAGS]
    ld [EN_SAVE+3], a
    ld a, 1
    ld [EN_DEPTH], a
    ld a, [EN_FLAGS]
    res FLAG_SYNC, a        ; we render the insert ourselves: cursor state stays valid
    ld [EN_FLAGS], a
    jr .setptr
.top:
    xor a
    ld [EN_TOP], a
    ld [EN_DEPTH], a
    ld [EN_INSERT], a
    ld a, c
    and FLAG_NEWS_MASK | FLAG_NOWRAP_MASK
    or FLAG_ACTIVE_MASK
    ld [EN_FLAGS], a
    push bc
    call InitLayout
    pop bc
    ld a, [$C0C8]
    ld [EN_SSTART], a
    ld a, [$C0C9]
    ld [EN_SSTART+1], a
.setptr:
    ld a, b
    ld [EN_BANK], a
    ld a, [EN_TMP]
    ld [EN_PTR], a
    ld a, [EN_TMP+1]
    ld [EN_PTR+1], a
    jp EnRun

; ---- HL in EN_STUB..+$0F : continue the current English stream
EnResume::
    xor a
    ld [EN_TOP], a
    ld [EN_INSERT], a
    ld a, [$4000]
    ld [EN_CBANK], a
    ld a, [EN_FLAGS]
    bit FLAG_ACTIVE, a
    jr nz, .active
    ld a, $FD               ; nothing to continue: behave like end-of-message
    jp Delegate
.active:
    bit FLAG_SYNC, a
    jr z, .nosync
    res FLAG_SYNC, a
    ld [EN_FLAGS], a
    call SyncCursor
    ld a, [EN_FLAGS]
.nosync:
    bit FLAG_PEND_PAGE, a
    jr z, .nopage
    res FLAG_PEND_PAGE, a
    ld [EN_FLAGS], a
    call ClearPage
    ld a, [EN_FLAGS]
.nopage:
    bit FLAG_PEND_F9, a
    jr z, EnRun
    res FLAG_PEND_F9, a
    set FLAG_SYNC, a
    ld [EN_FLAGS], a
    ld a, $F9
    jp Delegate

; ---------------------------------------------------------------- main loop
EnRun::
    call ReadByte
    cp $20
    jr c, EnRun             ; ignore stray low bytes
    cp $7F
    jr nc, EnControl
    ld [EN_CHAR], a
    cp ' '
    jr z, .space
    ld a, [EN_WSTART]
    and a
    jr z, .draw
    xor a
    ld [EN_WSTART], a
    call CheckWrap          ; may not return here (page break)
.draw:
    ld a, [EN_CHAR]
    call DrawChar
    jr .after
.space:
    call CurX
    cp EN_LMARGIN + 1
    jr c, .nodraw           ; no leading spaces at line start
    ld a, ' '
    call DrawChar
.nodraw:
    ld a, 1
    ld [EN_WSTART], a
.after:
    ld a, [$C0C4]
    bit 0, a
    jr nz, EnRun            ; instant mode: keep going
    ld a, [EN_DEPTH]
    and a
    jr nz, EnRun            ; inserts always render instantly
    ; typewriter: one character per call
    ld a, LOW(EN_TOKEN_CHR)
    ld [$C0DE], a
    ld a, HIGH(EN_TOKEN_CHR)
    ld [$C0DF], a
    ld a, [EN_CBANK]
    ld [rROMB], a
    ret

EnControl:
    cp $FD
    jp z, .end
    cp $FA
    jr z, .wait
    cp $FB
    jr z, .nl
    cp $FC
    jp z, .page
    cp $ED
    jr z, EnRun
    cp $F8
    jr z, .tab
    cp $80
    jp z, BackSpace
    cp $81
    jr z, .money
    cp $F9
    jr z, .sync
    cp $FF
    jp z, EnNumber
    cp $EA
    jp z, EnNumber
    cp $EB
    jp z, EnNumber
    cp $EC
    jp z, EnNumber
    cp $EE
    jp z, EnNumber
    cp $EF
    jr z, .sync
    ; name / word inserts (E0-E9, FE): the original handler recurses into $0A43
    ; If the insert is not English, the original renderer draws it: resync afterwards.
    ld b, a
    ld a, [EN_FLAGS]
    set FLAG_SYNC, a
    ld [EN_FLAGS], a
    ld a, 1
    ld [EN_WSTART], a
    ld [EN_INSERT], a
    ld a, b
    jp Delegate
.sync:
    ld b, a
    ld a, [EN_FLAGS]
    set FLAG_SYNC, a
    ld [EN_FLAGS], a
    ld a, b
    jp Delegate
.wait:
    ld a, LOW(EN_TOKEN_WAIT)
    ld [$C0DE], a
    ld a, HIGH(EN_TOKEN_WAIT)
    ld [$C0DF], a
    ld a, $FA
    jp Delegate
.money:
    ld a, 1
    ld [EN_NUMMODE], a
    jp EnRun
.nl:
    call NewLinePlain
    jp EnRun
.tab:
    call ReadByte           ; column index
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl              ; *32 bytes per column
    ld a, [EN_SSTART]
    ld e, a
    ld a, [EN_SSTART+1]
    ld d, a
    add hl, de              ; HL = target cursor
    ld a, l
    ld [EN_TMP], a
    ld a, h
    ld [EN_TMP+1], a
    ld a, [EN_PX]
    and a
    jr z, .tabblank
    call NextColumnAddr     ; finish the partly drawn column
.tabblank:
    call FreshColumn
.tabloop:
    ld a, [EN_TMP+1]
    ld b, a
    ld a, [$C0C9]
    cp b
    jr c, .tabclr
    jr nz, .tabdone
    ld a, [EN_TMP]
    ld b, a
    ld a, [$C0C8]
    cp b
    jr nc, .tabdone
.tabclr:
    call WriteCol           ; buffer is blank
    call NextColumnAddr
    jr .tabloop
.tabdone:
    ld a, [EN_TMP]
    ld [$C0C8], a
    ld a, [EN_TMP+1]
    ld [$C0C9], a
    call FreshColumn
    jp EnRun
.page:
    call ClearPage
    jp EnRun
.end:
    ld a, [EN_DEPTH]
    and a
    jr z, .endtop
    ; end of an insert: pop the outer stream
    xor a
    ld [EN_DEPTH], a
    ld a, [EN_SAVE]
    ld [EN_PTR], a
    ld a, [EN_SAVE+1]
    ld [EN_PTR+1], a
    ld a, [EN_SAVE+2]
    ld [EN_BANK], a
    ld a, [EN_FLAGS]
    res FLAG_SYNC, a        ; we drew the insert: keep cursor
    ld [EN_FLAGS], a
    ld a, $FD
    jr Delegate
.endtop:
    xor a
    ld [EN_FLAGS], a
    ld a, [EN_PX]
    and a
    jr z, .endcol
    ld a, [$C0C8]
    add 32
    ld [$C0C8], a
    ld a, [$C0C9]
    adc 0
    ld [$C0C9], a
.endcol:
    ld a, $FD
    ; fall through

; Run the original dispatcher on a single control byte placed in RAM.
; Handlers that continue jump back to $0A43 with HL inside EN_STUB -> EnResume.
Delegate::
    ld [EN_STUB], a
    ld a, [EN_CBANK]
    ld [rROMB], a
    ld hl, EN_STUB
    ld a, [hl+]
    cp $FF
    jp $0A46

; ---------------------------------------------------------------- stream access
; A = next byte of the English stream; advances EN_PTR. Clobbers HL.
ReadByte::
    ld a, [EN_BANK]
    ld [rROMB], a
    ld hl, EN_PTR
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ld a, [hl+]
    push af
    ld a, l
    ld [EN_PTR], a
    ld a, h
    ld [EN_PTR+1], a
    ld a, [EN_CBANK]
    ld [rROMB], a
    pop af
    ret

; Step EN_PTR back by one byte.
UnreadByte::
    ld hl, EN_PTR
    ld a, [hl]
    sub 1
    ld [hl+], a
    ld a, [hl]
    sbc 0
    ld [hl], a
    ret

; ---------------------------------------------------------------- layout
; Geometry from the game's box variables: page start $D686, line-2 start $C12E, box tiles $D66D.
InitLayout::
    ; line bytes = [$C12E] - [$D686]
    ld a, [$D686]
    ld e, a
    ld a, [$D687]
    ld d, a
    ld a, [$C12E]
    sub e
    ld l, a
    ld a, [$C12F]
    sbc d
    ld h, a
    ; sane? 64..1024 bytes and multiple of 32
    jr c, .default
    ld a, h
    cp 4
    jr nc, .default
    or l
    jr z, .default
    ld a, l
    and $1F
    jr nz, .default
    jr .have
.default:
    ld hl, 18*32
.have:
    ld a, l
    ld [EN_LBYTES], a
    ld a, h
    ld [EN_LBYTES+1], a
    ; lines = (tiles*16) / linebytes
    ld a, [$D66D]
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld b, 0
.div:
    ld a, [EN_LBYTES]
    ld c, a
    ld a, l
    sub c
    ld l, a
    ld a, [EN_LBYTES+1]
    ld c, a
    ld a, h
    sbc c
    ld h, a
    jr c, .divdone
    inc b
    jr .div
.divdone:
    ld a, b
    and a
    jr nz, .nlok
    ld b, 2
.nlok:
    ld a, b
    ld [EN_NLINES], a
    ; fall through

; Recompute line / column state from the cursor $C0C8 (start a fresh column).
SyncCursor::
    ; offset = c0c8 - d686 ; line = offset / lbytes ; linestart = d686 + line*lbytes
    ld a, [$D686]
    ld e, a
    ld a, [$D687]
    ld d, a
    ld a, [$C0C8]
    sub e
    ld l, a
    ld a, [$C0C9]
    sbc d
    ld h, a
    ld b, 0
    jr c, .neg
.div:
    ld a, [EN_LBYTES]
    ld c, a
    ld a, l
    sub c
    ld l, a
    ld a, [EN_LBYTES+1]
    ld c, a
    ld a, h
    sbc c
    ld h, a
    jr c, .got
    inc b
    jr .div
.neg:
.got:
    ld a, b
    ld [EN_LINE], a
    ; linestart = d686 + b*lbytes
    ld h, d
    ld l, e
.mul:
    ld a, b
    and a
    jr z, .mdone
    ld a, [EN_LBYTES]
    ld c, a
    ld a, [EN_LBYTES+1]
    push bc
    ld b, a
    add hl, bc
    pop bc
    dec b
    jr .mul
.mdone:
    ld a, l
    ld [EN_LSTART], a
    ld a, h
    ld [EN_LSTART+1], a
    ; fall through
FreshColumn::
    xor a
    ld [EN_PX], a
    ld hl, EN_COL
    ld b, 32
.clr:
    ld [hl+], a
    dec b
    jr nz, .clr
    ld a, 1
    ld [EN_WSTART], a
    ; wrapped text gets a left margin at the start of a line (label strips are laid out exactly)
    ld a, [EN_FLAGS]
    bit FLAG_NOWRAP, a
    ret nz
    call CurX
    and a
    ret nz
    ld a, EN_LMARGIN
    ld [EN_PX], a
    ret

; A = x position in pixels from the line start (0..255)
CurX::
    ld a, [EN_LSTART]
    ld e, a
    ld a, [EN_LSTART+1]
    ld d, a
    ld a, [$C0C8]
    sub e
    ld l, a
    ld a, [$C0C9]
    sbc d
    ld h, a                 ; HL = bytes from line start (32 per column)
    ; cols = HL >> 5 ; x = cols*8 + px  = HL >> 2 + px
    srl h
    rr l
    srl h
    rr l
    ld a, [EN_PX]
    add l
    ret

; Advance to the next line; if the box is full, wait for a button and start a new page.
; Called with nothing pending in the stream (or after the triggering char was un-read).
NewLine::
    ld a, [EN_FLAGS]
    bit FLAG_NEWS, a
    jr nz, NewLineNews
NewLinePlain::
    ld a, [EN_LINE]
    inc a
    ld b, a
    ld a, [EN_NLINES]
    cp b
    jr z, NewLineFull
    jr c, NewLineFull
    ld a, b
    ld [EN_LINE], a
    ld a, [EN_LSTART]
    ld l, a
    ld a, [EN_LSTART+1]
    ld h, a
    ld a, [EN_LBYTES]
    ld c, a
    ld a, [EN_LBYTES+1]
    ld b, a
    add hl, bc
    ld a, l
    ld [EN_LSTART], a
    ld [$C0C8], a
    ld a, h
    ld [EN_LSTART+1], a
    ld [$C0C9], a
    jp FreshColumn
NewLineFull:
    ld a, [EN_FLAGS]
    set FLAG_PEND_PAGE, a
    ld [EN_FLAGS], a
    jr NewLineWait
NewLineNews:
    ld a, [EN_FLAGS]
    set FLAG_PEND_F9, a
    ld [EN_FLAGS], a
NewLineWait:
    ; abandon the current call: wait for the button; EnResume performs the pending action
    pop hl                  ; drop our return address (NewLine callers are on the engine stack frame)
    ld a, [EN_RETSP]
    and a
    jr z, .noextra
    pop hl                  ; CheckWrap -> NewLine: drop one more frame
.noextra:
    xor a
    ld [EN_RETSP], a
    ld a, LOW(EN_TOKEN_WAIT)
    ld [$C0DE], a
    ld a, HIGH(EN_TOKEN_WAIT)
    ld [$C0DF], a
    ld a, $FA
    jp Delegate

; At the start of a word: if it does not fit on the current line, break the line first.
CheckWrap::
    ld a, [EN_FLAGS]
    bit FLAG_NOWRAP, a
    ret nz
    ; width of the word starting at EN_CHAR (already read) + following chars up to space/control
    ld a, [EN_CHAR]
    call GlyphAdvance
    ld c, a                 ; C = width
    ld a, [EN_PTR]
    ld l, a
    ld a, [EN_PTR+1]
    ld h, a
    ld a, [EN_BANK]
    ld [rROMB], a
.scan:
    ld a, [hl+]
    cp ' '+1
    jr c, .done
    cp $7F
    jr nc, .ctl
    push hl
    call GlyphAdvance
    pop hl
    add c
    jr c, .huge
    ld c, a
    jr .scan
.ctl:
    ; a name insert glued to the word counts as ~40 px
    cp $FE
    jr z, .ins
    cp $FA
    jr nc, .done
    cp $ED
    jr z, .scan
.ins:
    ld a, c
    add 40
    jr c, .huge
    ld c, a
    jr .done
.huge:
    ld c, $FF
.done:
    ld a, [EN_CBANK]
    ld [rROMB], a
    call CurX
    ld b, a
    cp EN_LMARGIN + 1
    ret c                   ; already at line start
    ld a, b
    add c
    jr c, .wrap
    dec a                   ; last column of the word (advance includes 1px spacing)
    ld b, a
    ld a, [EN_LBYTES]       ; line width in px = lbytes/4
    ld l, a
    ld a, [EN_LBYTES+1]
    ld h, a
    srl h
    rr l
    srl h
    rr l
    ld a, h
    and a
    ret nz                  ; > 255 px lines: never wrap
    ld a, l
    sub EN_RMARGIN
    ld l, a
    ld a, b
    cp l
    ret c
.wrap:
    call UnreadByte         ; re-read this char after the break
    ld a, 1
    ld [EN_RETSP], a
    call NewLine            ; returns only if the line break stayed inside the box
    xor a
    ld [EN_RETSP], a
    ; continue with the char on the new line
    call ReadByte
    ld [EN_CHAR], a
    ret

; A = char -> A = advance in px (width + 1)
GlyphAdvance::
    sub $20
    ld e, a
    ld d, 0
    ld hl, FontWidths
    add hl, de
    ld a, [hl]
    inc a
    ret

; ---------------------------------------------------------------- drawing
; Draw char A at (C0C8, EN_PX), advance.
DrawChar::
    sub $20
    ld e, a
    ld d, 0
    ld hl, FontWidths
    add hl, de
    ld a, [hl]
    inc a
    ld [EN_ADV], a
    ; rows = FontRows + idx*12
    ld h, d
    ld l, e
    add hl, hl
    add hl, de              ; *3
    add hl, hl
    add hl, hl              ; *12
    ld de, FontRows
    add hl, de
    ld de, EN_COL+2
    ld b, 12
.row:
    push bc
    ld a, [hl+]
    push hl
    ld h, a
    ld l, 0
    ld a, [EN_PX]
    and a
    jr z, .noshift
.sh:
    srl h
    rr l
    dec a
    jr nz, .sh
.noshift:
    ld a, [de]
    or h
    ld [de], a
    ld a, e
    add 16
    ld c, a                 ; EN_NEXT row = EN_COL row + 16 (same page)
    ld b, d
    ld a, [bc]
    or l
    ld [bc], a
    inc de
    pop hl
    pop bc
    dec b
    jr nz, .row
    call WriteCol
    ld a, [EN_ADV]
    ld b, a
    ld a, [EN_PX]
    add b
    cp 8
    jr nc, .nextcol
    ld [EN_PX], a
    ret
.nextcol:
    sub 8
    ld [EN_PX], a
    ; cursor += 32, column buffer <- next buffer
    ld a, [$C0C8]
    add 32
    ld [$C0C8], a
    ld a, [$C0C9]
    adc 0
    ld [$C0C9], a
    ld hl, EN_COL+16
    ld de, EN_COL
    ld b, 16
.mv:
    ld a, [hl]
    ld [de], a
    xor a
    ld [hl+], a
    inc de
    dec b
    jr nz, .mv
    jp WriteCol

; ---------------------------------------------------------------- numbers
; The game keeps numbers as decimal digit buffers (one byte 0-9 per digit) in units of 10,000 for money.
; We print them ourselves: no leading zeros, and in money mode (prefix $81) x10,000 with thousands separators.
EnNumber::
    ld c, 0                 ; C bit0 = negative (debt)
    cp $FF
    jr nz, .notff
    ld hl, $C16C
    ld b, 7
    jr .print
.notff:
    cp $EA
    jr nz, .notea
    ld hl, $D6A4
    ld b, 7
    jr .print
.notea:
    cp $EB
    jr nz, .noteb
    ld a, [$D6D0]
    and a
    jr z, .plain
    jr .debt
.noteb:
    cp $EC
    jr nz, .plain
    call PlayerDebt
    jr z, .plain
.debt:
    ld hl, $C222
    ld b, 6
    ld c, 1
    jr .print
.plain:
    ld hl, $C221
    ld b, 7
.print:
    ; collect significant digits as ASCII into EN_NUMBUF, E = count
    ld de, EN_NUMBUF
.skip:
    ld a, [hl]
    and a
    jr nz, .copy
    inc hl
    dec b
    jr nz, .skip
    ld a, '0'               ; value is zero
    ld [de], a
    inc de
    jr .digits_done
.copy:
    ld a, [hl+]
    add '0'
    ld [de], a
    inc de
    dec b
    jr nz, .copy
    ld a, [EN_NUMMODE]
    and a
    jr z, .digits_done
    ld a, '0'
    ld b, 4
.x10k:
    ld [de], a
    inc de
    dec b
    jr nz, .x10k
.digits_done:
    ld a, e
    sub LOW(EN_NUMBUF)
    ld [EN_NUMLEN], a
    ; draw: sign, then digits with separators every 3 from the right (money mode)
    ld a, c
    and a
    jr z, .nosign
    ld a, '-'
    call DrawChar
.nosign:
    ld hl, EN_NUMBUF
.draw:
    ld a, [EN_NUMLEN]
    and a
    jr z, .end
    ld b, a
    ld a, [EN_NUMMODE]
    and a
    jr z, .nosep
    ld a, l
    cp LOW(EN_NUMBUF)
    jr z, .nosep            ; never before the first digit
    ld a, b
.mod3:
    sub 3
    jr z, .sep
    jr nc, .mod3
    jr .nosep
.sep:
    push hl
    ld a, ','
    call DrawChar
    pop hl
.nosep:
    ld a, [hl+]
    push hl
    call DrawChar
    pop hl
    ld a, [EN_NUMLEN]
    dec a
    ld [EN_NUMLEN], a
    jr .draw
.end:
    xor a
    ld [EN_NUMMODE], a
    ld [EN_WSTART], a
    jp EnRun.after

; ---- money field for non-text callers: 9 columns (72 px) at [C0C8], right-aligned "$12,340,000"
NumFieldDebt::
    ld de, $C222
    ld b, 6
    ld c, 1
    jr NumFieldGo
NumField::
    ld b, 7
    ld c, 0
NumFieldGo:
    ; save the text engine's drawing state (a dialog may be mid-render)
    push bc
    push de
    ld hl, EN_PX
    ld de, EN_FSAVE
    ld a, [hl]
    ld [de], a
    inc de
    ld hl, EN_COL
    ld b, 32
.sv:
    ld a, [hl+]
    ld [de], a
    inc de
    dec b
    jr nz, .sv
    pop de
    pop bc
    ; build "-$1,234,0000" text in EN_NUMBUF (NUL terminated)
    call FormatMoney
    ; width in px
    ld hl, EN_NUMBUF
    ld c, 0
.w:
    ld a, [hl+]
    and a
    jr z, .wd
    push hl
    call GlyphAdvance
    pop hl
    add c
    ld c, a
    jr .w
.wd:
    ; render into the RAM field buffer (no visible partial states), then copy to VRAM in one pass
    ld a, [$C0C8]
    ld [EN_FSTART], a
    ld a, [$C0C9]
    ld [EN_FSTART+1], a
    xor a
    ld [EN_PX], a
    ld hl, EN_COL
    ld b, 32
.clr:
    ld [hl+], a
    dec b
    jr nz, .clr
    ld hl, EN_FIELD
    ld b, 9*16
.clrf:
    ld [hl+], a
    dec b
    jr nz, .clrf
    ld a, 1
    ld [EN_WRAM], a
    ; start x = 72 - width (+1 for the trailing spacing of the last glyph)
    ld a, 73
    sub c
    jr nc, .xok
    xor a
.xok:
    ld b, a
    and 7
    ld [EN_PX], a
    ld a, b
    srl a
    srl a
    srl a                   ; columns
    ld l, a
    ld h, 0
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, [EN_FSTART]
    ld e, a
    ld a, [EN_FSTART+1]
    ld d, a
    add hl, de
    ld a, l
    ld [$C0C8], a
    ld a, h
    ld [$C0C9], a
    ld hl, EN_NUMBUF
.dr:
    ld a, [hl+]
    and a
    jr z, .done
    push hl
    call DrawChar
    pop hl
    jr .dr
.done:
    xor a
    ld [EN_WRAM], a
    ; copy the 9 columns to VRAM (each byte to both bitplanes)
    ld a, [EN_FSTART]
    ld l, a
    ld a, [EN_FSTART+1]
    ld h, a
    ld de, EN_FIELD
    ld b, 9*16
.cp:
    ldh a, [rSTAT]
    bit 1, a
    jr nz, .cp
    ld a, [de]
    ld [hl+], a
    ld [hl+], a
    inc de
    dec b
    jr nz, .cp
    ; cursor = field end
    ld a, l
    ld [$C0C8], a
    ld a, h
    ld [$C0C9], a
    ; restore engine state
    ld hl, EN_FSAVE
    ld a, [hl+]
    ld [EN_PX], a
    ld de, EN_COL
    ld b, 32
.rs:
    ld a, [hl+]
    ld [de], a
    inc de
    dec b
    jr nz, .rs
    ret

; DE = digit buffer, B = digits, C = 1 if negative -> EN_NUMBUF = "[-]$d,ddd,dd0,000" NUL-terminated (x10,000)
FormatMoney::
    ld hl, EN_NUMBUF
    ld a, c
    and a
    jr z, .pos
    ld a, '-'
    ld [hl+], a
.pos:
    ld a, '$'
    ld [hl+], a
    ; skip leading zeros
.skip:
    ld a, [de]
    and a
    jr nz, .sig
    inc de
    dec b
    jr nz, .skip
    ld a, '0'               ; zero
    ld [hl+], a
    xor a
    ld [hl], a
    ret
.sig:
    ; digits remaining (B) + 4 trailing zeros = total; separators before positions where remaining % 3 == 0
    ld a, b
    add 4
    ld c, a                 ; C = digits left to emit
.emit:
    ld a, c
    and a
    jr z, .fin
    cp 4
    jr nc, .real
    ld a, '0'               ; trailing zeros (x10,000)
    jr .put
.real:
    ld a, c
    cp 5
    jr c, .zero4
    ld a, [de]
    inc de
    add '0'
    jr .put
.zero4:
    ld a, '0'
.put:
    ld [hl+], a
    dec c
    ld a, c
    and a
    jr z, .fin
.mod:
    sub 3
    jr z, .comma
    jr nc, .mod
    jr .emit
.comma:
    ld a, ','
    ld [hl+], a
    jr .emit
.fin:
    xor a
    ld [hl], a
    ret

; Z set if the current player has no debt (mirrors bank $14:$58C7)
PlayerDebt::
    ld a, $14
    ld [rROMB], a
    ld a, [$C21C]
    ld l, a
    ld h, 0
    add hl, hl
    ld de, $5230
    add hl, de
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ld de, $003A
    add hl, de
    ld b, [hl]
    ld a, [EN_CBANK]
    ld [rROMB], a
    ld a, b
    and a
    ret

; $80: back up into the previous column (re-read it from VRAM) so the next glyph sits EN_BACKPX px into it.
BackSpace::
    ld a, [$C0C8]
    sub 32
    ld [$C0C8], a
    ld l, a
    ld a, [$C0C9]
    sbc 0
    ld [$C0C9], a
    ld h, a
    ld de, EN_COL
    ld b, 16
.r:
    ldh a, [rSTAT]
    bit 1, a
    jr nz, .r
    ld a, [hl+]
    inc hl
    ld [de], a
    inc de
    dec b
    jr nz, .r
    ld hl, EN_COL+16
    xor a
    ld b, 16
.c:
    ld [hl+], a
    dec b
    jr nz, .c
    ld a, 8 - EN_BACKPX
    ld [EN_PX], a
    jp EnRun

; cursor += 32
NextColumnAddr::
    ld a, [$C0C8]
    add 32
    ld [$C0C8], a
    ld a, [$C0C9]
    adc 0
    ld [$C0C9], a
    ret

; Write the 16-row column buffer to VRAM at [C0C8] (each row byte to both bitplanes).
WriteCol::
    ld a, [EN_WRAM]
    and a
    jr nz, WriteColRam
    ld a, [$C0C8]
    ld l, a
    ld a, [$C0C9]
    ld h, a
    ld de, EN_COL
    ld b, 16
.w:
    ldh a, [rSTAT]
    bit 1, a
    jr nz, .w
    ld a, [de]
    ld [hl+], a
    ld [hl+], a
    inc de
    dec b
    jr nz, .w
    ret

; RAM-target variant: column (C0C8 - EN_FSTART)/32 of the field buffer, 16 bytes per column
WriteColRam:
    ld a, [EN_FSTART]
    ld e, a
    ld a, [EN_FSTART+1]
    ld d, a
    ld a, [$C0C8]
    sub e
    ld l, a
    ld a, [$C0C9]
    sbc d
    ld h, a
    srl h
    rr l                    ; /2 : 16 bytes per column
    ld de, EN_FIELD
    add hl, de
    ld de, EN_COL
    ld b, 16
.c:
    ld a, [de]
    ld [hl+], a
    inc de
    dec b
    jr nz, .c
    ret

; New page: clear the box like the original FC handler and restart at its top-left.
ClearPage::
    ld a, [$D6A2]
    ld l, a
    ld a, [$D6A3]
    ld h, a
    ld a, [$D66D]
    ld d, a
    ld e, $01
    call $0A0B
    ld a, [$D686]
    ld [$C0C8], a
    ld [EN_LSTART], a
    ld a, [$D687]
    ld [$C0C9], a
    ld [EN_LSTART+1], a
    xor a
    ld [EN_LINE], a
    jp FreshColumn

INCLUDE "font.inc"
