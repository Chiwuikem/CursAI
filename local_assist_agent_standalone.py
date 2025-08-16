
# Local Assist Agent — Standalone (tools-first)
# Search recent files and move selected ones to Trash/Recycle Bin safely.
#
# Usage:
#   pip install send2trash
#   python local_assist_agent_standalone.py "delete the exe I downloaded yesterday"
#   python local_assist_agent_standalone.py --execute "delete the setup file I downloaded today"
#
import argparse, time, sys
from pathlib import Path
from send2trash import send2trash

DEFAULT_SCOPES = [Path.home()/'Downloads', Path.home()/'Desktop', Path.home()/'Documents']
RISKY_PATTERNS = ['.ssh','AppData','Library','Program Files','Windows','System32','/bin','/sbin','/usr','/etc']

def find_recent(roots, patterns=('*.exe',), days=14, name_hint=None):
    cutoff = time.time() - days*86400
    hits = []
    for root in roots:
        rp = Path(root).expanduser()
        if not rp.exists(): continue
        for pat in patterns:
            for p in rp.rglob(pat):
                try:
                    st = p.stat()
                    if st.st_mtime >= cutoff and (not name_hint or name_hint.lower() in p.name.lower()):
                        hits.append((p, st.st_mtime, st.st_size))
                except Exception:
                    pass
    hits.sort(key=lambda h: h[1], reverse=True)
    return hits

def show_hits(hits):
    if not hits:
        print("No candidates found.")
        return
    print("\nCandidates (newest first):")
    for i,h in enumerate(hits,1):
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h[1]))
        print(f"{i:>2}. {h[0].name:40}  {h[0]}  |  {int(h[2]//1024)} KB  |  {ts}")

def select(hits):
    if not hits:
        return []
    sel = input("\nPick numbers (e.g. 1,3-5) or Enter to cancel: ").strip()
    if not sel: return []
    idxs=set()
    for part in sel.split(','):
        part=part.strip()
        if '-' in part:
            a,b = part.split('-',1)
            if a.isdigit() and b.isdigit():
                idxs.update(range(int(a), int(b)+1))
        elif part.isdigit():
            idxs.add(int(part))
    return [hits[i-1][0] for i in sorted(idxs) if 1<=i<=len(hits)]

def risky(paths):
    out=[]
    for p in paths:
        s=str(p).lower()
        if any(pat.lower() in s for pat in RISKY_PATTERNS):
            out.append(p)
    return out

def main():
    ap = argparse.ArgumentParser(description="Local Assist Agent — Standalone")
    ap.add_argument('prompt', type=str)
    ap.add_argument('--execute', action='store_true', help='Actually move to Trash (default is dry-run)')
    a = ap.parse_args()

    p = a.prompt.lower()
    if 'delete' in p and '.exe' in p:
        days = 2 if ('today' in p or 'yesterday' in p) else 14
        patterns = ['*.exe']
    elif 'delete' in p:
        days = 14
        patterns = ['*']
    else:
        print("Try: delete the exe I downloaded yesterday")
        sys.exit(0)

    hits = find_recent(DEFAULT_SCOPES, patterns=patterns, days=days)
    show_hits(hits)
    targets = select(hits)
    if not targets:
        print("No selection. Bye.")
        return

    rk = risky(targets)
    if rk:
        print("\nWARNING: Some selections look system-like. Double-check:")
        for p in rk: print(" -", p)
        if input("Type 'I UNDERSTAND' to keep going: ").strip() != "I UNDERSTAND":
            print("Aborted.")
            return

    print("\nReady to move to Trash:")
    for pth in targets: print(" -", pth)

    if not a.execute:
        print("\nDry-run: re-run with --execute to actually delete.")
        return

    if input("Type 'yes' to confirm: ").strip().lower()!='yes':
        print("Cancelled.")
        return

    ok=0; errs=[]
    for pth in targets:
        try:
            send2trash(str(pth)); ok+=1
        except Exception as e:
            errs.append((pth, e))
    print(f"Moved {ok} item(s) to Trash.")
    if errs:
        print("Errors:")
        for pth,e in errs:
            print(" -", pth, "->", e)

if __name__=='__main__':
    main()
