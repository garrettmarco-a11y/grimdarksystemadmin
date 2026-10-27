"""Tkinter presentation layer. Renders GameState; game rules live in gdsa.simulation."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from .simulation import FOOD_UPKEEP_AMOUNT, GameState, add_starting_tasks

class GDSAGui:
    """Main GUI class for the Grimdark System Admin game"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Grimdark System Admin")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize game
        self.game = GameState()
        self._initialize_game_tasks()
        
        # Automation controls
        self.is_running = False
        self.current_speed = "Normal"  # Speed used when Play is pressed; the game starts paused
        self.speed_intervals = {
            "Slow": 2000,      # 2 seconds per tick
            "Normal": 1000,    # 1 second per tick
            "Fast": 500,       # 0.5 seconds per tick
            "Paused": None
        }
        self.automation_job = None
        
        # Setup GUI
        self._setup_styles()
        self._create_widgets()
        self._update_display()
        
    def _initialize_game_tasks(self):
        """Add starting tasks to the game"""
        add_starting_tasks(self.game)

    def _setup_styles(self):
        """Setup ttk styles for dark theme"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure dark theme
        self.style.configure('TFrame', background='#2b2b2b')
        self.style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
        self.style.configure('Title.TLabel', background='#2b2b2b', foreground='#ffffff', font=('Arial', 12, 'bold'))
        self.style.configure('TButton', background='#404040', foreground='#ffffff')
        self.style.map('TButton', 
                      background=[('active', '#505050'), ('pressed', '#303030'), ('disabled', '#606060')])
        self.style.configure('TNotebook', background='#2b2b2b')
        self.style.configure('TNotebook.Tab', background='#404040', foreground='#ffffff')
        self.style.map('TNotebook.Tab',
                      background=[('selected', '#505050')])
    
    def _create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="GRIMDARK SYSTEM ADMIN", style='Title.TLabel', font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Top panel - Status and Controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Day and Tribute info
        self.status_frame = ttk.Frame(top_frame)
        self.status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.day_label = ttk.Label(self.status_frame, text="Day 1", font=('Arial', 14, 'bold'))
        self.day_label.pack(anchor=tk.W)
        
        self.tribute_label = ttk.Label(self.status_frame, text="Imperial Tribute Due: 7 days")
        self.tribute_label.pack(anchor=tk.W)
        
        self.food_upkeep_label = ttk.Label(self.status_frame, text="Food Upkeep Due: 6 days")
        self.food_upkeep_label.pack(anchor=tk.W)
        
        # Controls
        controls_frame = ttk.Frame(top_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        # Speed controls frame
        speed_frame = ttk.Frame(controls_frame)
        speed_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Speed label
        speed_label = ttk.Label(speed_frame, text="Automation:", font=('Arial', 10, 'bold'))
        speed_label.pack(side=tk.TOP)
        
        # Speed buttons frame
        speed_buttons_frame = ttk.Frame(speed_frame)
        speed_buttons_frame.pack(side=tk.TOP)
        
        # Play/Pause button
        self.play_pause_button = ttk.Button(speed_buttons_frame, text="▶️ Play", command=self._toggle_play_pause, width=8)
        self.play_pause_button.pack(side=tk.LEFT, padx=(0, 2))
        
        # Speed selection buttons
        self.slow_button = ttk.Button(speed_buttons_frame, text="Slow", command=lambda: self._set_speed("Slow"), width=6)
        self.slow_button.pack(side=tk.LEFT, padx=1)
        
        self.normal_button = ttk.Button(speed_buttons_frame, text="Normal", command=lambda: self._set_speed("Normal"), width=7)
        self.normal_button.pack(side=tk.LEFT, padx=1)
        
        self.fast_button = ttk.Button(speed_buttons_frame, text="Fast", command=lambda: self._set_speed("Fast"), width=6)
        self.fast_button.pack(side=tk.LEFT, padx=1)
        
        # Current speed indicator
        self.speed_indicator = ttk.Label(speed_frame, text="Speed: Paused", font=('Arial', 9))
        self.speed_indicator.pack(side=tk.TOP, pady=(2, 0))
        
        # Manual controls frame
        manual_frame = ttk.Frame(controls_frame)
        manual_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        manual_label = ttk.Label(manual_frame, text="Manual:", font=('Arial', 10, 'bold'))
        manual_label.pack(side=tk.TOP)
        
        self.tick_button = ttk.Button(manual_frame, text="Single Tick", command=self._advance_tick, width=10)
        self.tick_button.pack(side=tk.TOP)
        
        # New game button
        self.new_game_button = ttk.Button(controls_frame, text="New Game", command=self._new_game)
        self.new_game_button.pack(side=tk.LEFT)
        
        # Main content area with notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Resources tab
        self._create_resources_tab()
        
        # Subordinates tab
        self._create_subordinates_tab()
        
        # Tasks tab
        self._create_tasks_tab()
        
        # Events tab
        self._create_events_tab()
    
    def _create_resources_tab(self):
        """Create the resources tab"""
        resources_frame = ttk.Frame(self.notebook)
        self.notebook.add(resources_frame, text="Resources")
        
        # Resources display
        resources_label = ttk.Label(resources_frame, text="RESOURCE STOCKPILES", style='Title.TLabel')
        resources_label.pack(pady=(10, 20))
        
        self.resources_frame = ttk.Frame(resources_frame)
        self.resources_frame.pack(fill=tk.X, padx=20)
        
        # Create resource displays
        self.material_label = ttk.Label(self.resources_frame, text="Materials: 50", font=('Arial', 12))
        self.material_label.pack(anchor=tk.W, pady=5)
        
        self.biologics_label = ttk.Label(self.resources_frame, text="Biologics (food): 30", font=('Arial', 12))
        self.biologics_label.pack(anchor=tk.W, pady=5)
        
        self.minerals_label = ttk.Label(self.resources_frame, text="Minerals: 20", font=('Arial', 12))
        self.minerals_label.pack(anchor=tk.W, pady=5)
    
    def _create_subordinates_tab(self):
        """Create the subordinates tab"""
        subordinates_frame = ttk.Frame(self.notebook)
        self.notebook.add(subordinates_frame, text="Subordinates")
        
        subordinates_label = ttk.Label(subordinates_frame, text="YOUR SUBORDINATES", style='Title.TLabel')
        subordinates_label.pack(pady=(10, 20))
        
        # Scrollable frame for subordinates
        canvas = tk.Canvas(subordinates_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(subordinates_frame, orient="vertical", command=canvas.yview)
        self.subordinates_scrollable_frame = ttk.Frame(canvas)
        
        self.subordinates_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.subordinates_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 20))
    
    def _create_tasks_tab(self):
        """Create the tasks tab"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="Tasks")
        
        tasks_label = ttk.Label(tasks_frame, text="ACTIVE TASKS", style='Title.TLabel')
        tasks_label.pack(pady=(10, 20))
        
        # Create task assignment interface
        assignment_frame = ttk.Frame(tasks_frame)
        assignment_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        ttk.Label(assignment_frame, text="Assign Task:").pack(side=tk.LEFT)
        
        self.subordinate_var = tk.StringVar()
        self.subordinate_combo = ttk.Combobox(assignment_frame, textvariable=self.subordinate_var, width=20)
        self.subordinate_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(assignment_frame, text="to").pack(side=tk.LEFT)
        
        self.task_var = tk.StringVar()
        self.task_combo = ttk.Combobox(assignment_frame, textvariable=self.task_var, width=30)
        self.task_combo.pack(side=tk.LEFT, padx=(10, 5))
        
        assign_button = ttk.Button(assignment_frame, text="Assign", command=self._assign_task)
        assign_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Scrollable frame for tasks
        canvas = tk.Canvas(tasks_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(tasks_frame, orient="vertical", command=canvas.yview)
        self.tasks_scrollable_frame = ttk.Frame(canvas)
        
        self.tasks_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.tasks_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 20))
    
    def _create_events_tab(self):
        """Create the events tab"""
        events_frame = ttk.Frame(self.notebook)
        self.notebook.add(events_frame, text="Events Log")
        
        events_label = ttk.Label(events_frame, text="EVENTS LOG", style='Title.TLabel')
        events_label.pack(pady=(10, 20))
        
        # Events text area
        self.events_text = scrolledtext.ScrolledText(
            events_frame,
            wrap=tk.WORD,
            height=25,
            bg='#1a1a1a',
            fg='#ffffff',
            font=('Courier', 10)
        )
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
    
    def _update_display(self):
        """Update all display elements"""
        self._update_status()
        self._update_resources()
        self._update_subordinates()
        self._update_tasks()
        self._update_events()
        self._update_comboboxes()
        self._update_speed_buttons()
    
    def _update_status(self):
        """Update status display"""
        self.day_label.config(text=f"Day {self.game.day}")
        
        if self.game.imperial_tribute_due <= 3:
            tribute_text = f"⚠️ Imperial Tribute Due: {self.game.imperial_tribute_due} days ({self.game.imperial_tribute_amount} Materials)"
        else:
            tribute_text = f"Imperial Tribute Due: {self.game.imperial_tribute_due} days ({self.game.imperial_tribute_amount} Materials)"
        self.tribute_label.config(text=tribute_text)
        
        # Warn when current stores would not cover the next upkeep
        upkeep_text = f"Food Upkeep Due: {self.game.food_upkeep_due_in} days ({FOOD_UPKEEP_AMOUNT} Biologics)"
        if self.game.resources.biologics < FOOD_UPKEEP_AMOUNT:
            upkeep_text = "⚠️ " + upkeep_text
        self.food_upkeep_label.config(text=upkeep_text)
    
    def _update_resources(self):
        """Update resources display"""
        resources = self.game.resources
        for label, name, amount in (
            (self.material_label, "Materials", resources.materials),
            (self.biologics_label, "Biologics (food)", resources.biologics),
            (self.minerals_label, "Minerals", resources.minerals),
        ):
            text = f"{name}: {amount}"
            if amount < 0:
                text += " ⚠️ DEFICIT"
            label.config(text=text)
    
    def _update_subordinates(self):
        """Update subordinates display"""
        # Clear existing widgets
        for widget in self.subordinates_scrollable_frame.winfo_children():
            widget.destroy()
        
        for subordinate in self.game.subordinates:
            sub_frame = ttk.Frame(self.subordinates_scrollable_frame)
            sub_frame.pack(fill=tk.X, pady=10, padx=10)
            
            # Name and current task
            name_text = subordinate.name
            if subordinate.current_task:
                name_text += f" (Working on: {subordinate.current_task})"
            
            name_label = ttk.Label(sub_frame, text=name_text, font=('Arial', 12, 'bold'))
            name_label.pack(anchor=tk.W)
            
            # Stats
            stats_text = f"Logistics: {subordinate.logistics} | Security: {subordinate.security} | Intelligence: {subordinate.intelligence}"
            stats_label = ttk.Label(sub_frame, text=stats_text)
            stats_label.pack(anchor=tk.W)
            
            # Need
            if subordinate.need:
                need_text = f"Need: {subordinate.need}"
                if subordinate.need_fulfilled:
                    need_text += " ✅"
                else:
                    need_text += " ❌"
                need_label = ttk.Label(sub_frame, text=need_text)
                need_label.pack(anchor=tk.W)
            
            # Separator
            separator = ttk.Frame(sub_frame, height=2)
            separator.pack(fill=tk.X, pady=(10, 0))
    
    def _update_tasks(self):
        """Update tasks display"""
        # Clear existing widgets
        for widget in self.tasks_scrollable_frame.winfo_children():
            widget.destroy()
        
        for task in self.game.tasks:
            task_frame = ttk.Frame(self.tasks_scrollable_frame)
            task_frame.pack(fill=tk.X, pady=10, padx=10)
            
            # Task name and area
            name_label = ttk.Label(task_frame, text=f"{task.name} ({task.area.value})", font=('Arial', 12, 'bold'))
            name_label.pack(anchor=tk.W)
            
            # Progress bar
            progress_frame = ttk.Frame(task_frame)
            progress_frame.pack(fill=tk.X, pady=5)
            
            progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate')
            progress_bar['value'] = task.completion_percentage
            progress_bar.pack(side=tk.LEFT)
            
            progress_label = ttk.Label(progress_frame, text=f"{task.progress}/{task.required_progress} ({task.completion_percentage:.1f}%)")
            progress_label.pack(side=tk.LEFT, padx=(10, 0))
            
            # Assignment
            if task.assigned_subordinate:
                assigned_label = ttk.Label(task_frame, text=f"Assigned to: {task.assigned_subordinate}")
                assigned_label.pack(anchor=tk.W)
            
            # Description
            if task.description:
                desc_label = ttk.Label(task_frame, text=f"Description: {task.description}")
                desc_label.pack(anchor=tk.W)
            
            # Separator
            separator = ttk.Frame(task_frame, height=2)
            separator.pack(fill=tk.X, pady=(10, 0))
    
    def _update_events(self):
        """Update events log"""
        self.events_text.delete('1.0', tk.END)
        
        # Show recent events (last 50)
        recent_events = self.game.events_log[-50:] if len(self.game.events_log) > 50 else self.game.events_log
        
        for event in recent_events:
            self.events_text.insert(tk.END, event + "\n")
        
        # Scroll to bottom
        self.events_text.see(tk.END)
    
    def _update_comboboxes(self):
        """Update combobox values"""
        subordinate_names = [sub.name for sub in self.game.subordinates]
        self.subordinate_combo['values'] = subordinate_names
        
        task_names = [task.name for task in self.game.tasks]
        self.task_combo['values'] = task_names
    
    def _advance_tick(self):
        """Advance the game by one tick"""
        self.game.advance_tick()
        self._update_display()
        
        # Show any urgent messages
        if self.game.tribute_outcome == "paid":
            messagebox.showinfo(
                "Imperial Tribute",
                f"Imperial tribute of {self.game.imperial_tribute_amount} Materials has been paid.",
            )
        elif self.game.tribute_outcome == "failed":
            messagebox.showwarning("Imperial Tribute", "Warning: Insufficient materials for Imperial tribute!")
    
    def _assign_task(self):
        """Assign a subordinate to a task"""
        subordinate_name = self.subordinate_var.get()
        task_name = self.task_var.get()
        
        if subordinate_name and task_name:
            if self.game.assign_subordinate_to_task(subordinate_name, task_name):
                messagebox.showinfo("Assignment", f"{subordinate_name} assigned to {task_name}")
                self._update_display()
            else:
                reason = self.game.assignment_error(subordinate_name, task_name) or "Could not assign subordinate to task"
                messagebox.showerror("Assignment Failed", reason)
        else:
            messagebox.showwarning("Assignment", "Please select both a subordinate and a task")
    
    def _new_game(self):
        """Start a new game"""
        result = messagebox.askyesno("New Game", "Are you sure you want to start a new game?")
        if result:
            # Stop automation
            self._stop_automation()
            
            # Reset game
            self.game = GameState()
            self._initialize_game_tasks()
            self._update_display()
    
    def _toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.is_running:
            self._pause_automation()
        else:
            self._start_automation()
    
    def _set_speed(self, speed):
        """Set the automation speed"""
        self.current_speed = speed
        if self.is_running:
            self._stop_automation()
            self._start_automation()
        else:
            self._update_speed_buttons()
    
    def _start_automation(self):
        """Start automated ticking"""
        if self.current_speed != "Paused" and self.current_speed in self.speed_intervals:
            self.is_running = True
            interval = self.speed_intervals[self.current_speed]
            self._schedule_next_tick(interval)
            self._update_speed_buttons()
    
    def _pause_automation(self):
        """Pause automated ticking"""
        self._stop_automation()
        self._update_speed_buttons()
    
    def _stop_automation(self):
        """Stop automated ticking"""
        self.is_running = False
        if self.automation_job:
            self.root.after_cancel(self.automation_job)
            self.automation_job = None
    
    def _schedule_next_tick(self, interval):
        """Schedule the next automated tick"""
        if self.is_running:
            self.automation_job = self.root.after(interval, self._automated_tick)
    
    def _automated_tick(self):
        """Perform an automated tick"""
        if self.is_running:
            self._advance_tick()
            interval = self.speed_intervals[self.current_speed]
            self._schedule_next_tick(interval)
    
    def _update_speed_buttons(self):
        """Update the appearance of speed control buttons"""
        # Update play/pause button
        if self.is_running:
            self.play_pause_button.config(text="⏸️ Pause")
        else:
            self.play_pause_button.config(text="▶️ Play")
        
        # Update speed indicator
        if self.is_running:
            self.speed_indicator.config(text=f"Speed: {self.current_speed}")
        else:
            self.speed_indicator.config(text=f"Speed: Paused ({self.current_speed})")
        
        # Update speed button styles (highlight current speed)
        speed_buttons = {
            "Slow": self.slow_button,
            "Normal": self.normal_button,
            "Fast": self.fast_button
        }
        
        for speed_name, button in speed_buttons.items():
            if speed_name == self.current_speed and self.is_running:
                # Highlight active speed
                button.config(state='disabled')
            else:
                button.config(state='normal')
