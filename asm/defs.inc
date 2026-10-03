DEF rROMB  EQU $2100
DEF rSTAT  EQU $FF41
DEF EN_TBL_BANK EQU $58

; engine RAM (unused WRAM0 region, verified idle across 42 save states)
DEF EN_FLAGS  EQU $C780
DEF EN_PTR    EQU $C781   ; 2
DEF EN_BANK   EQU $C783
DEF EN_PX     EQU $C784
DEF EN_LINE   EQU $C785
DEF EN_NLINES EQU $C786
DEF EN_LBYTES EQU $C787   ; 2
DEF EN_LSTART EQU $C789   ; 2
DEF EN_CBANK  EQU $C78B
DEF EN_DEPTH  EQU $C78C
DEF EN_SAVE   EQU $C78D   ; 4
DEF EN_TOP    EQU $C791
DEF EN_WSTART EQU $C792
DEF EN_CHAR   EQU $C793
DEF EN_ADV    EQU $C794
DEF EN_RETSP  EQU $C795
DEF EN_TMP    EQU $C796   ; 2
DEF EN_INSERT EQU $C798
DEF EN_SSTART EQU $C799   ; 2
DEF EN_NUMMODE EQU $C79B
DEF EN_NUMLEN EQU $C79C
DEF EN_STUB   EQU $C7A0   ; 16: delegate stub; any HL in $C7A0-$C7AF resumes English
DEF EN_TOKEN_CHR  EQU $C7A8
DEF EN_TOKEN_WAIT EQU $C7AA
DEF EN_NUMBUF EQU $C7D0   ; 16
DEF EN_COL    EQU $C7B0   ; 16 rows current column + 16 rows next column (same 256-byte page)

DEF FLAG_ACTIVE    EQU 0
DEF FLAG_NEWS      EQU 1
DEF FLAG_PEND_PAGE EQU 2
DEF FLAG_PEND_F9   EQU 3
DEF FLAG_SYNC      EQU 4
DEF FLAG_NOWRAP    EQU 5
DEF FLAG_NOWRAP_MASK EQU 1 << FLAG_NOWRAP
DEF FLAG_NOMARGIN   EQU 6
DEF FLAG_NOMARGIN_MASK EQU 1 << FLAG_NOMARGIN
DEF FLAG_CENTER8    EQU 7
DEF FLAG_CENTER8_MASK EQU 1 << FLAG_CENTER8
DEF FLAG_ACTIVE_MASK EQU 1 << FLAG_ACTIVE
DEF FLAG_NEWS_MASK   EQU 1 << FLAG_NEWS
DEF EN_BACKPX EQU 3       ; how far '0K' tucks back against a printed number
DEF EN_LMARGIN EQU 3      ; px of padding at the start of each wrapped line
DEF EN_RMARGIN EQU 2      ; px kept free at the end of each wrapped line
DEF EN_FSAVE  EQU $C800   ; 33: saved PX + column buffers while drawing a money field
DEF EN_FSTART EQU $C821   ; 2
DEF EN_WRAM   EQU $C823   ; 1: WriteCol targets EN_FIELD instead of VRAM
DEF EN_FIELD  EQU $C830   ; 144: 9-column money field buffer (1bpp rows)
DEF EN_BURST  EQU $C824   ; chars drawn in the current typewriter call
DEF EN_CPF    EQU 3       ; typewriter speed: characters per frame
DEF EN_FALIGN EQU $C825   ; money field: 0 = right-aligned 9 columns, 1 = left-aligned, minimal
DEF EN_FCOLS  EQU $C826
