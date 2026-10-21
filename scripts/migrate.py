from eventops.migrations import VERSION
from eventops.store import Store

if __name__ == "__main__":
    Store()
    print(f"Companion additive schema upgrades applied through version {VERSION}.")
