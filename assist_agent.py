import argparse
from local_assist_agent.main import run as run_agent
from local_assist_agent.config import DEFAULT_SCOPES

def main():
    parser = argparse.ArgumentParser(description="Local Assist Agent (MVP)")
    parser.add_argument("prompt", nargs="?", help="e.g., 'delete the exe I downloaded yesterday'")
    parser.add_argument("--execute", action="store_true", help="Actually move to Trash (default: dry-run)")
    parser.add_argument("--scopes", type=str, help="Comma-separated allowed roots (optional)")
    parser.add_argument("--preview", action="store_true", help="Open OS file browser to selected files before deletion")
    args = parser.parse_args()

    scopes = [p.strip() for p in args.scopes.split(",")] if args.scopes else DEFAULT_SCOPES
    run_agent(args.prompt, execute=args.execute, scopes=scopes, preview=args.preview)

if __name__ == "__main__":
    main()
