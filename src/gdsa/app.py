"""Application entry point."""

import argparse
import tkinter as tk

from .ui import GDSAGui

def main(argv=None):
    """Main function to run the GUI"""
    parser = argparse.ArgumentParser(description="Grimdark System Admin")
    parser.add_argument("--debug", action="store_true",
                        help="show the read-only population debug tab")
    args = parser.parse_args(argv)
    
    root = tk.Tk()
    app = GDSAGui(root, debug=args.debug)
    
    # Ensure automation stops when window is closed
    def on_closing():
        app._stop_automation()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
