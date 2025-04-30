import tkinter as tk
from PIL import Image, ImageTk 
from tkinter import messagebox, filedialog
from tkinter import ttk  
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import random  
from itertools import product

# --- Payoff Matrix ---
payoff_matrix = {
    ("Ε", "Α"): (+5,-5),
    ("Η", "Α"): (+2,-2),
    ("Ε", "Π"): (+3,-3),
    ("Η", "Π"): (+1,-1),
}

extended_payoff_matrix = {
    ("Α", "Ε", "Ε"): (-8, -5, +10),
    ("Α", "Η", "Ε"): (-6, -3, +9),
    ("Π", "Ε", "Ε"): (-4, -1, +7),
    ("Π", "Η", "Ε"): (-2, +1, +5),
    ("Α", "Ε", "Η"): (-5, -3, +6),
    ("Α", "Η", "Η"): (-2, -1, +4),
    ("Π", "Ε", "Η"): (-1, 0, +2),
    ("Π", "Η", "Η"): (0, +1, +1),
}

supermarket_modes = ["Εξ'αρχής", "Ενδιάμεσα", "Ποτέ"]
rounds = 30
supermarket_mode = "Ενδιάμεσα"
supermarket_entry_round = 5
game_mode = "2 Παίκτες"

class RLAgent:
    def __init__(self, name, actions, epsilon=0.05, seed=None):
        self.name = name
        self.epsilon = epsilon
        self.actions = actions
        self.scores = {a: 0 for a in actions}
        self.counts = {a: 1e-6 for a in actions}
        self.rng = random.Random(seed)  
        self.initial_strategies_used = set()

    def choose_strategy(self):
    # Ensure each strategy is tried at least once
        for action in self.actions:
            if action not in self.initial_strategies_used:
                self.initial_strategies_used.add(action)
                print(f"{self.name} initial trial: {action}")
                return action

        # Then follow epsilon-greedy logic
        if self.rng.random() < self.epsilon:
            strategy = self.rng.choice(self.actions)
            print(f"{self.name} δοκιμάζει: {strategy}")
            return strategy

        avg = {k: self.scores[k] / self.counts[k] for k in self.actions}
        best = max(avg, key=avg.get)
        print(f"{self.name} επωφελείται από: {best}")
        return best


    def update(self, strategy, payoff):
        self.scores[strategy] += payoff
        self.counts[strategy] += 1

# --- UI Setup ---
def clear_and_switch_frame(root, state, new_frame):
    current = state.get("current_frame")
    if current:
        current.destroy()
    new_frame.pack(fill="both", expand=True)
    state["current_frame"] = new_frame

# --- Simulation Core ---
def run_simulation():
    if game_mode == "2 Παίκτες":
        history = {"Τοπικά": [], "Σουπερμάρκετ": []}
        local_agent = RLAgent("Τοπικά", ["Α", "Π"], epsilon=0.1, seed=1)
        supermarket_agent = RLAgent("Σουπερμάρκετ", ["Ε", "Η"], epsilon=0.1, seed=2)
        supermarket_strategy = None
        local_counts = {"Α": 0, "Π": 0}
        supermarket_counts = {"Ε": 0, "Η": 0}

        for r in range(rounds):
            # Determine if the supermarket is participating
            if (supermarket_mode == "Εξ'αρχής") or \
            (supermarket_mode == "Ενδιάμεσα" and r >= supermarket_entry_round):
                supermarket_strategy = supermarket_agent.choose_strategy()
            elif supermarket_mode == "Ποτέ":
                supermarket_strategy = None

            # Local agent always acts
            local_strategy = local_agent.choose_strategy()

            # Calculate payoffs
            if supermarket_strategy:
                result = payoff_matrix.get((supermarket_strategy, local_strategy), (0, 0))
                sup_payoff, loc_payoff = result
            else:
                sup_payoff, loc_payoff = 0, 1  # Default: supermarket not active

            # Record payoffs
            history["Σουπερμάρκετ"].append(sup_payoff)
            history["Τοπικά"].append(loc_payoff)

            # Update agents
            local_agent.update(local_strategy, loc_payoff)
            local_counts[local_strategy] += 1

            if supermarket_strategy:
                supermarket_agent.update(supermarket_strategy, sup_payoff)
                supermarket_counts[supermarket_strategy] += 1

    elif game_mode == "3 Παίκτες":
        history = {"Τοπικά": [], "Σουπερμάρκετ": [], "Εμπορικό": []}

        local1_agent = RLAgent("Τοπικά", actions=["Α", "Π"])      
        local2_agent = RLAgent("Σουπερμάρκετ", actions=["Ε", "Η"])      

        for r in range(rounds):
            local1 = local1_agent.choose_strategy()
            local2 = local2_agent.choose_strategy()

            if (supermarket_mode == "Εξ'αρχής") or \
               (supermarket_mode == "Ενδιάμεσα" and r >= supermarket_entry_round):
                supermarket_strategy = "Ε" if r % 2 == 0 else "Η"
            else:
                supermarket_strategy = "Η"

            key = (local1, local2, supermarket_strategy)
            if key in extended_payoff_matrix:
                l1p, l2p, sp = extended_payoff_matrix[key]
            else:
                raise ValueError(f"Missing key in extended_payoff_matrix: {key}")

            history["Τοπικά"].append(l1p)
            history["Σουπερμάρκετ"].append(l2p)
            history["Εμπορικό"].append(sp)

            local1_agent.update(local1, l1p)
            local2_agent.update(local2, l2p)

        # For display summary
        local_counts = {
            "Α": int(local1_agent.counts.get("Α", 0) + local2_agent.counts.get("Α", 0)),
            "Π": int(local1_agent.counts.get("Π", 0)),}

    return history, local_counts

# --- Screens ---
def show_start_screen(root, state):
    image = Image.open("shops.png")
    bg_image = ImageTk.PhotoImage(image)
    state['bg_image'] = bg_image 
    frame = tk.Frame(root)
    clear_and_switch_frame(root, state, frame)
    title = tk.Label(frame, text="Προσομοίωση Τοπικής Αγοράς", font=("Helvetica", 26, "bold"),
                     bg="#ffffff", fg="#000000")
    title.pack(pady=(30, 10))
    image_label = tk.Label(frame, image=bg_image)
    image_label.pack(pady=10)
    start_btn = tk.Button(frame, text="Έναρξη Προσομοίωσης", font=("Helvetica", 16),
                          bg="#4CAF50", fg="white",
                          command=lambda: run_simulation_screen(root, state))
    start_btn.pack(pady=10)
    param_btn = tk.Button(frame, text="Ορισμός Παραμέτρων", font=("Helvetica", 16),
                          bg="#2196F3", fg="white",
                          command=lambda: show_parameter_screen(root, state))
    param_btn.pack(pady=10)

def show_parameter_screen(root, state):
    frame = tk.Frame(root, bg="#e3f2fd")
    clear_and_switch_frame(root, state, frame)

    tk.Label(frame, text="Ορισμός παραμέτρων προσομοίωσης", font=("Helvetica", 22, "bold"), bg="#e3f2fd").pack(pady=20)
    rounds_var = tk.IntVar(value=rounds)
    supermarket_mode_var = tk.StringVar(value=supermarket_mode)
    supermarket_entry_var = tk.IntVar(value=supermarket_entry_round)
    game_modes = ["2 Παίκτες", "3 Παίκτες"]
    game_mode_var = tk.StringVar(value=game_mode)

    def add_labeled_entry(label, var):
        row = tk.Frame(frame, bg="#e3f2fd")
        tk.Label(row, text=label, font=("Helvetica", 16), bg="#e3f2fd", width=25, anchor='w').pack(side="left", padx=5)
        tk.Entry(row, textvariable=var, font=("Helvetica", 16)).pack(side="left")
        row.pack(pady=4)

    add_labeled_entry("Πλήθος Γύρων (Max 100):", rounds_var)
    add_labeled_entry("Γύρος Ένταξης Σουπερμάρκετ:", supermarket_entry_var)
    # Ετικέτα
    tk.Label(frame, text="Έλευση Σουπερμάρκετ:", font=("Helvetica", 16), bg="#e3f2fd").pack(pady=(15, 5))

    # OptionMenu με ρύθμιση μεγέθους
    supermarket_menu = tk.OptionMenu(frame, supermarket_mode_var, *supermarket_modes)
    supermarket_menu.config(font=("Helvetica", 16), width=20)
    supermarket_menu.pack(pady=5)

    # Ετικέτα
    tk.Label(frame, text="Λειτουργία:", font=("Helvetica", 16), bg="#e3f2fd").pack(pady=(10, 5))

    # OptionMenu με ρύθμιση μεγέθους
    game_mode_menu = tk.OptionMenu(frame, game_mode_var, *game_modes)
    game_mode_menu.config(font=("Helvetica", 16), width=20)
    game_mode_menu.pack(pady=5)
    #Μεγαλύτερη γραμματοσειρά στο drop-down OptionMenu
    supermarket_menu["menu"].config(font=("Helvetica", 16))
    game_mode_menu["menu"].config(font=("Helvetica", 16))

    def apply_and_run():
        global rounds, supermarket_mode, supermarket_entry_round, game_mode
        rounds = min(rounds_var.get(), 100)
        supermarket_mode = supermarket_mode_var.get()
        supermarket_entry_round = supermarket_entry_var.get()
        game_mode = game_mode_var.get()

        history, local_counts = run_simulation()

        if len(history["Τοπικά"]) == 0 or len(history["Σουπερμάρκετ"]) == 0:
            messagebox.showerror("Σφάλμα", "Τα δεδομένα προσομοίωσης δεν είναι έτοιμα.")
        else:
            run_simulation_screen(root, state)

    tk.Button(frame, text="Έναρξη Προσομοίωσης", font=("Helvetica", 16), bg="#4CAF50", fg="white",
              command=apply_and_run).pack(pady=20)
    tk.Button(frame, text="Επεξεργασία Πινάκων Κερδών", font=("Helvetica", 16), bg="#9C27B0", fg="white",
          command=edit_payoff_matrices).pack(pady=10)
    tk.Button(frame, text="Πίσω", font=("Helvetica", 16), bg="#e91e63", fg="white",
              command=lambda: show_start_screen(root, state)).pack()

def edit_payoff_matrices():
    matrix_window = tk.Toplevel()
    matrix_window.title("Επεξεργασία Πινάκων Κερδών")
    matrix_window.geometry("800x600")
    style = ttk.Style()
    style.configure("TNotebook.Tab", font=("Helvetica", 12), padding=[10, 5])
    tab_control = ttk.Notebook(matrix_window)

    tab_2p = tk.Frame(tab_control)
    tab_control.add(tab_2p, text='2 Παίκτες')

    tk.Label(tab_2p, text="Πίνακας Κερδών 2 παικτών (Σουπερμάρκετ, Τοπικά):",
             font=("Helvetica", 18, "bold")).pack(pady=10)

    entries_2p = {}
    for i, key in enumerate([("Ε", "Α"), ("Η", "Α"), ("Ε", "Π"), ("Η", "Π")]):
        row = tk.Frame(tab_2p)
        tk.Label(row, text=str(key), font=("Helvetica", 16), width=20).pack(side="left", padx=10)
        e = tk.Entry(row, width=25, font=("Helvetica", 16))
        e.insert(0, str(payoff_matrix.get(key, (0, 0))))
        e.pack(side="left", padx=10, pady=5)
        entries_2p[key] = e
        row.pack(pady=5)

    tab_3p = tk.Frame(tab_control)
    tab_control.add(tab_3p, text='3 Παίκτες')

    tk.Label(tab_3p, text="Πίνακας Κερδών 3 παικτών (Τοπικά, Σουπερμάρκετ, Εμπορικό):", font=("Helvetica", 18, "bold")).pack(pady=10)

    entries_3p = {}
    for key in extended_payoff_matrix:
        row = tk.Frame(tab_3p)
        tk.Label(row, text=str(key), font=("Helvetica", 16), width=25).pack(side="left", padx=10)
        e = tk.Entry(row, width=30, font=("Helvetica", 16))
        e.insert(0, str(extended_payoff_matrix.get(key, (0, 0, 0))))
        e.pack(side="left", padx=10, pady=5)
        entries_3p[key] = e
        row.pack(pady=5)

    tab_control.pack(expand=1, fill="both")

    def apply_changes():
        global payoff_matrix, extended_payoff_matrix
        for k, entry in entries_2p.items():
            try:
                payoff_matrix[k] = tuple(map(int, entry.get().strip("() ").split(",")))
            except:
                messagebox.showerror("Invalid Input", f"Invalid value for key {k} in 2-player matrix.")

        for k, entry in entries_3p.items():
            try:
                extended_payoff_matrix[k] = tuple(map(int, entry.get().strip("() ").split(",")))
            except:
                messagebox.showerror("Invalid Input", f"Invalid value for key {k} in 3-player matrix.")

        matrix_window.destroy()

    tk.Button(matrix_window, text="Εφαρμογή", bg="#4CAF50", fg="white",
              font=("Helvetica", 16), width=15, height=2,
              command=apply_changes).pack(pady=20)

def run_simulation_screen(root, state):
    frame = tk.Frame(root, bg="#fefcfb")
    clear_and_switch_frame(root, state, frame)

    history, local_counts = run_simulation()
    rounds_range = list(range(len(history["Τοπικά"])))

    fig, ax = plt.subplots(figsize=(9, 5))
    if "Εμπορικό" in history:
        ax.plot(rounds_range, history["Εμπορικό"], label="Εμπορικό", marker="x")
    ax.plot(rounds_range, history["Τοπικά"], label="Τοπικά", marker="o")
    ax.plot(rounds_range, history["Σουπερμάρκετ"], label="Σουπερμάρκετ", marker="s")

    ax.set_title("Προσδοκώμενα Κέρδη με την πάροδο του χρόνου")
    ax.set_xlabel("Γύρος")
    ax.set_ylabel("Προσδοκώμενο Κέρδος")
    ax.grid(True)
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(pady=10)
    canvas.draw()

    if game_mode == "2 Παίκτες":
        summary = f"Αντίσταση: {local_counts['Α']} rounds, Προσαρμογή: {local_counts['Π']} rounds"
    else:
        summary = f"Συνολικές στρατηγικές: Αντίσταση: {local_counts['Α']} rounds, Προσαρμογή: {local_counts['Π']} rounds"

    tk.Label(frame, text=summary, font=("Helvetica", 12), bg="#fefcfb").pack(pady=10)

    def export_results():
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF File", "*.pdf"), ("PNG Image", "*.png")])
        if path:
            if path.endswith(".pdf"):
                with PdfPages(path) as pdf:
                    pdf.savefig(fig)
            else:
                fig.savefig(path)
                
    def export_to_txt():
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text File", "*.txt")],
                                            title="Αποθήκευση αρχείου .txt")
        if path:
            # Αν το widget είναι read-only, προσωρινή ενεργοποίηση
            text_widget.config(state="normal")
            content = text_widget.get("1.0", "end-1c")
            text_widget.config(state="disabled")

            with open(path, "w", encoding="utf-8") as file:
                file.write(content)

    btn_frame = tk.Frame(frame, bg="#fefcfb")
    btn_frame.pack()
    tk.Button(btn_frame, text="Εξαγωγή Αποτελεσμάτων", font=("Helvetica", 14), bg="#2196F3", fg="white",
              command=export_results).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Αρχική", font=("Helvetica", 14), bg="#d32f2f", fg="white",
              command=lambda: show_start_screen(root, state)).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Εξαγωγή Κειμένου Ανάλυσης", font=("Helvetica", 14), bg="#ffa500", fg="white",
              command=export_to_txt).pack(side="left", padx=10)

    # Check zero-sum (2-player)
    is_zero_sum_2p = all(s + l == 0 for (s, l) in payoff_matrix.values())

    # Check zero-sum (3-player)
    is_zero_sum_3p = all(sum(p) == 0 for p in extended_payoff_matrix.values())

    # --- 2-Player Analysis ---

    def find_nash_equilibria_2p(matrix, supermarket_actions, local_actions):
        nash_eqs = []
        for s_a, l_a in product(supermarket_actions, local_actions):
            s_payoff, l_payoff = matrix[(s_a, l_a)]

            s_best_response = all(matrix[(other_s, l_a)][0] <= s_payoff for other_s in supermarket_actions)
            l_best_response = all(matrix[(s_a, other_l)][1] <= l_payoff for other_l in local_actions)

            if s_best_response and l_best_response:
                nash_eqs.append((s_a, l_a))
        return nash_eqs

    def find_pareto_efficient(matrix):
        efficient = []
        all_outcomes = list(matrix.items())
        for (a1, p1) in all_outcomes:
            dominated = False
            for (a2, p2) in all_outcomes:
                if a1 == a2:
                    continue
                if all(x >= y for x, y in zip(p2, p1)) and any(x > y for x, y in zip(p2, p1)):
                    dominated = True
                    break
            if not dominated:
                efficient.append((a1, p1))
        return efficient

    # --- 3-Player Analysis ---

    def find_nash_equilibria_3p(matrix, actions1, actions2, actions3):
        nash_eqs = []
        for a1, a2, a3 in product(actions1, actions2, actions3):
            if (a1, a2, a3) not in matrix:
                continue  # Skip missing entries

            p_current = matrix[(a1, a2, a3)]

            best1 = all(matrix.get((alt1, a2, a3), (-float('inf'), 0, 0))[0] <= p_current[0] for alt1 in actions1)
            best2 = all(matrix.get((a1, alt2, a3), (0, -float('inf'), 0))[1] <= p_current[1] for alt2 in actions2)
            best3 = all(matrix.get((a1, a2, alt3), (0, 0, -float('inf')))[2] <= p_current[2] for alt3 in actions3)

            if best1 and best2 and best3:
                nash_eqs.append(((a1, a2, a3), p_current))
        return nash_eqs


    # --- Build Analysis String ---

    analysis = ""

    if game_mode == "2 Παίκτες":
        supermarket_actions = ["Ε", "Η"]
        local_actions = ["Α", "Π"]
        nash_equilibria = find_nash_equilibria_2p(payoff_matrix, supermarket_actions, local_actions)
        pareto_efficient = find_pareto_efficient(payoff_matrix)

        analysis += f"Παίγνιο Μηδενικού Αθροίσματος: {'Ναι' if is_zero_sum_2p else 'Όχι'}\n"
        analysis += "Καθαρή Στρατηγική - Ισορροπία Νash:\n"
        if nash_equilibria:
            for eq in nash_equilibria:
                analysis += f"  - {eq}\n"
        else:
            analysis += "  - Δεν βρέθηκε\n"

        analysis += "Αποδοτικά κατα Pareto αποτελέσματα:\n"
        for outcome, payoff in pareto_efficient:
            analysis += f"  - {outcome} με εκτιμώμενα κέρδη {payoff}\n"

    elif game_mode == "3 Παίκτες":
        actions1 = ["Α", "Π"]
        actions2 = ["Ε", "Η"]
        actions3 = ["Ε", "Η"]
        nash_eqs_3p = find_nash_equilibria_3p(extended_payoff_matrix, actions1, actions2, actions3)
        pareto_efficient_3p = find_pareto_efficient(extended_payoff_matrix)

        analysis += f"Παίγνιο Μηδενικού Αθροίσματος: {'Ναι' if is_zero_sum_3p else 'Όχι'}\n"
        analysis += "Καθαρή Στρατηγική - Ισορροπία Νash:\n"
        if nash_eqs_3p:
            for (a, p) in nash_eqs_3p:
                analysis += f"  - {a} με εκτιμώμενα κέρδη {p}\n"
        else:
            analysis += "  - Δεν βρέθηκε\n"

        analysis += "Αποδοτικά κατα Pareto αποτελέσματα:\n"
        for outcome, payoff in pareto_efficient_3p:
            analysis += f"  - {outcome} με εκτιμώμενα κέρδη {payoff}\n"

    # --- Display on GUI ---
    result_frame = tk.Frame(frame, bg="#fefcfb")
    result_frame.pack(fill="both", expand=True, padx=10, pady=10)

    text_widget = tk.Text(result_frame, wrap="word", font=("Helvetica", 11),
                        bg="#fefcfb", fg="black", height=15)
    text_widget.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(result_frame, command=text_widget.yview)
    scrollbar.pack(side="right", fill="y")

    text_widget.configure(yscrollcommand=scrollbar.set)
    text_widget.tag_configure("center", justify="center")

    # Εισαγωγή κάθε γραμμής ξεχωριστά με στοίχιση κέντρου
    lines = ("Ανάλυση βάσει Θεωρίας Παιγνίων:\n" + analysis).split("\n")
    for line in lines:
        text_widget.insert("end", line + "\n")
        text_widget.tag_add("center", f"end-{len(line)+1}c linestart", "end-1c")

    text_widget.config(state="disabled")  # read-only

# --- Launch ---
def launch_ui():
    root = tk.Tk()
    root.title("Προσομοίωση Τοπικής Αγοράς")
    root.state("zoomed") 
    state = {"current_frame": None}
    show_start_screen(root, state)
    root.mainloop()

launch_ui()
