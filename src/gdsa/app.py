"""Application entry point."""

import tkinter as tk

from .ui import GDSAGui

def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = GDSAGui(root)
    
    # Ensure automation stops when window is closed
    def on_closing():
        app._stop_automation()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
