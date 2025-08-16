import argparse

def main():
    ap = argparse.ArgumentParser(description="Local Assist Agent (MVP)")
    ap.add_argument("prompt", nargs="?", help="e.g., 'delete the exe I downloaded yesterday'")
    ap.add_argument("--execute", action="store_true", help="Actually move to Trash (default: dry-run)")
    ap.add_argument("--scopes", help="Comma-separated allowed roots (opttional)")
    args= ap.parse_args()

    if args.prompt:
        print("Scaffold ready. Next steps will implement actions.")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

