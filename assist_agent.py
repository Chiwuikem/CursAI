import argparse

from local_assist_agent.main import run as run_agent  # absolute import from the package

def main():
    ap = argparse.ArgumentParser(description="Local Assist Agent (MVP)")
    ap.add_argument("prompt", type=str, help="e.g., 'delete the exe I downloaded today'")
    ap.add_argument("--execute", action="store_true", help="Actually move to Recycle Bin (default: dry-run)")
    ap.add_argument("--scopes", type=str, default=None, help="Comma-separated allowed roots")
    args = ap.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",")] if args.scopes else None
    run_agent(args.prompt, execute=args.execute, scopes=scopes)

if __name__ == "__main__":
    main()
