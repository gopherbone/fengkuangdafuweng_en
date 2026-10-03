import os
import sys
SAMEBOY = os.environ.get("SAMEBOY_CLI", os.path.expanduser("~/sameboy-cli"))
sys.path.insert(0, os.path.join(SAMEBOY, "cli", "py"))
from gbemu import GBEmu
EMU = os.environ.get("GBEMU", os.path.join(SAMEBOY, "build", "gbemu"))

def boot(rom, model="cgb", seed=1, sav=None):
    g = GBEmu(EMU)
    g.__enter__()
    kw = dict(model=model, seed=seed)
    if sav: kw["sav"] = sav
    g.load_rom(rom, **kw)
    return g
