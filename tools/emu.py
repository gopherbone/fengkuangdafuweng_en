import sys
sys.path.insert(0, "/Users/nick/sameboy-cli/cli/py")
from gbemu import GBEmu
EMU = "/Users/nick/sameboy-cli/build/gbemu"

def boot(rom, model="cgb", seed=1, sav=None):
    g = GBEmu(EMU)
    g.__enter__()
    kw = dict(model=model, seed=seed)
    if sav: kw["sav"] = sav
    g.load_rom(rom, **kw)
    return g
