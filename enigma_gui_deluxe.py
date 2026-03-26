
import string
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

ALPHABET = string.ascii_uppercase

ROTOR_WIRINGS = {
    "I": ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II": ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV": ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V": ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}

REFLECTORS = {
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL"
}


class Rotor:
    def __init__(self, wiring, notch, ring=0, pos=0):
        self.wiring = wiring
        self.notch = notch
        self.ring = ring
        self.pos = pos

    def step(self):
        self.pos = (self.pos + 1) % 26

    def at_notch(self):
        return ALPHABET[self.pos] in self.notch

    def forward(self, c):
        i = (ALPHABET.index(c) + self.pos - self.ring) % 26
        return ALPHABET[(ALPHABET.index(self.wiring[i]) - self.pos + self.ring) % 26]

    def backward(self, c):
        i = (ALPHABET.index(c) + self.pos - self.ring) % 26
        return ALPHABET[(self.wiring.index(ALPHABET[i]) - self.pos + self.ring) % 26]


class Reflector:
    def __init__(self, wiring):
        self.wiring = wiring

    def reflect(self, c):
        return self.wiring[ALPHABET.index(c)]


class Plugboard:
    def __init__(self, pairs=""):
        self.map = {}
        pairs = pairs.upper().split()
        for p in pairs:
            if len(p) == 2:
                a, b = p
                self.map[a] = b
                self.map[b] = a

    def swap(self, c):
        return self.map.get(c, c)


class Enigma:
    def __init__(self, rotors, reflector, plugboard):
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = plugboard

    def step_rotors(self):
        if self.rotors[1].at_notch():
            self.rotors[0].step()
            self.rotors[1].step()
        elif self.rotors[2].at_notch():
            self.rotors[1].step()
        self.rotors[2].step()

    def encrypt_char(self, c):
        if c not in ALPHABET:
            return c
        self.step_rotors()
        c = self.plugboard.swap(c)
        for r in reversed(self.rotors):
            c = r.forward(c)
        c = self.reflector.reflect(c)
        for r in self.rotors:
            c = r.backward(c)
        c = self.plugboard.swap(c)
        return c


class EnigmaGUI:
    def __init__(self, root):
        self.root = root
        root.title("Enigma Machine Deluxe")

        self.build_controls()
        self.build_keyboard()
        self.build_lampboard()

    def build_controls(self):
        frame = tk.Frame(self.root)
        frame.pack()

        self.rotor_vars = []
        self.pos_vars = []
        self.ring_vars = []

        for i in range(3):
            col = tk.Frame(frame)
            col.pack(side=tk.LEFT, padx=5)

            var = tk.StringVar(value="I")
            ttk.Combobox(col, textvariable=var, values=list(ROTOR_WIRINGS.keys()), width=5).pack()
            self.rotor_vars.append(var)

            pos = tk.StringVar(value="A")
            tk.Entry(col, textvariable=pos, width=3).pack()
            self.pos_vars.append(pos)

            ring = tk.IntVar(value=0)
            tk.Entry(col, textvariable=ring, width=3).pack()
            self.ring_vars.append(ring)

        self.reflector_var = tk.StringVar(value="B")
        ttk.Combobox(frame, textvariable=self.reflector_var, values=["B", "C"], width=5).pack(side=tk.LEFT)

        self.plug_entry = tk.Entry(frame, width=20)
        self.plug_entry.pack(side=tk.LEFT)

        tk.Button(frame, text="Save", command=self.save_config).pack(side=tk.LEFT)
        tk.Button(frame, text="Load", command=self.load_config).pack(side=tk.LEFT)

    def build_machine(self):
        rotors = []
        for i in range(3):
            wiring, notch = ROTOR_WIRINGS[self.rotor_vars[i].get()]
            pos = ALPHABET.index(self.pos_vars[i].get().upper())
            ring = self.ring_vars[i].get()
            rotors.append(Rotor(wiring, notch, ring, pos))

        reflector = Reflector(REFLECTORS[self.reflector_var.get()])
        plugboard = Plugboard(self.plug_entry.get())

        return Enigma(rotors, reflector, plugboard)

    def press_key(self, char):
        machine = self.build_machine()
        result = machine.encrypt_char(char)
        self.light_up(result)

    def build_keyboard(self):
        frame = tk.Frame(self.root)
        frame.pack()

        for i, c in enumerate(ALPHABET):
            btn = tk.Button(frame, text=c, width=3, command=lambda ch=c: self.press_key(ch))
            btn.grid(row=i//9, column=i%9)

    def build_lampboard(self):
        self.lamps = {}
        frame = tk.Frame(self.root)
        frame.pack()

        for i, c in enumerate(ALPHABET):
            lbl = tk.Label(frame, text=c, width=3, bg="black", fg="white")
            lbl.grid(row=i//9, column=i%9)
            self.lamps[c] = lbl

    def light_up(self, char):
        for c in self.lamps:
            self.lamps[c].config(bg="black")
        self.lamps[char].config(bg="yellow")

    def save_config(self):
        data = {
            "rotors": [v.get() for v in self.rotor_vars],
            "positions": [v.get() for v in self.pos_vars],
            "rings": [v.get() for v in self.ring_vars],
            "reflector": self.reflector_var.get(),
            "plugboard": self.plug_entry.get()
        }
        file = filedialog.asksaveasfilename(defaultextension=".json")
        if file:
            with open(file, "w") as f:
                json.dump(data, f)

    def load_config(self):
        file = filedialog.askopenfilename()
        if file:
            with open(file) as f:
                data = json.load(f)
            for i in range(3):
                self.rotor_vars[i].set(data["rotors"][i])
                self.pos_vars[i].set(data["positions"][i])
                self.ring_vars[i].set(data["rings"][i])
            self.reflector_var.set(data["reflector"])
            self.plug_entry.delete(0, tk.END)
            self.plug_entry.insert(0, data["plugboard"])


if __name__ == "__main__":
    root = tk.Tk()
    app = EnigmaGUI(root)
    root.mainloop()
