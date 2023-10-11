import customtkinter as ctk
import tkinter
from PIL import Image
import os


# angepasste Variante von https://mail.python.org/pipermail/tkinter-discuss/2012-January/003041.html
# autocomplete funktioniert nicht perfekt, deswegen benutze ich nur die SearchCombobox
# vervollständigt automatisch, wenn man zu schnell tippt, oft falsches Wort
class AutocompleteCombobox(ctk.CTkComboBox):
    def __init__(self, master, completion_list, variable):
        super().__init__(master, values=completion_list, variable=variable)
        """Use our completion list as our drop down selection menu, arrows move through menu."""
        self._completion_list = sorted(completion_list, key=str.lower)  # Work with a sorted list
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def autocomplete(self, delta=0):
        """autocomplete the Combobox, delta may be 0/1/-1 to cycle through possible hits"""
        if delta:  # need to delete selection otherwise we would fix the current position
            self._entry.delete(self.position, tkinter.END)
        else:  # set position to end so selection starts where textentry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):  # Match case insensitively
                _hits.append(element)
        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the autocompletion
        if self._hits:
            self._entry.delete(0, tkinter.END)
            self._entry.insert(0, self._hits[self._hit_index])
            self._entry.select_range(self.position, tkinter.END)

    def handle_keyrelease(self, event):
        """event handler for the keyrelease event on this widget"""
        # Match list to input
        value = event.widget.get()

        if value == '':
            self.configure(values=self._completion_list)
        else:
            data = []
            for item in self._completion_list:
                if value.lower() in item.lower():
                    data.append(item)
            self.configure(values=data)

        if event.keysym == "BackSpace":
            self._entry.delete(self._entry.index(tkinter.INSERT), tkinter.END)
            self.position = self._entry.index(tkinter.END)
        if event.keysym == "Left":
            if self.position < self._entry.index(tkinter.END):  # delete the selection
                self._entry.delete(self.position, tkinter.END)
            else:
                self.position = self.position - 1  # delete one character
                self._entry.delete(self.position, tkinter.END)
        if event.keysym == "Right":
            self.position = self._entry.index(tkinter.END)  # go to end (no selection)
        if len(event.keysym) == 1:
            self.autocomplete()


class SearchCombobox(ctk.CTkComboBox):
    def __init__(self, master, values, variable):
        super().__init__(master, values=values, variable=variable)
        self.values = values
        self.bind("<KeyRelease>", self.handle_keyrelease)

    def _open_dropdown_menu(self):
        self._dropdown_menu.open(self.winfo_rootx() + 145,
                                 self.winfo_rooty() + self._apply_widget_scaling(self._current_height + 0))

    def handle_keyrelease(self, event):
        value = event.widget.get()

        if value == '':
            self.configure(values=self.values)
        else:
            data = []
            for item in self.values:
                if value.lower() in item.lower():
                    data.append(item)
            self.configure(values=data)


class CustomSizeEntryFrame(ctk.CTkFrame):
    def __init__(self, master, label_text, width, variable, insert_text):
        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)

        self.label = ctk.CTkLabel(self, text=label_text, anchor="e")
        self.entry = ctk.CTkEntry(self, width=width, textvariable=variable)
        self.entry.insert(0, insert_text)
        self.entry.delete(len(insert_text))

        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry.grid(row=0, column=1, padx=10, pady=10, sticky="e")


class CustomSizeFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)
        self.columns = ctk.IntVar()
        self.rows = ctk.IntVar()

        """
        self.column_label = ctk.CTkLabel(self, text="Anzahl Spalten: ")
        self.row_label = ctk.CTkLabel(self, text="Anzahl Reihen: ")
        self.column_entry = ctk.CTkEntry(self, width=40, textvariable=self.columns)
        self.row_entry = ctk.CTkEntry(self, width=40, textvariable=self.rows)
        self.column_entry.insert(0, "9")
        self.row_entry.insert(0, "6")
        self.column_entry.delete(1)
        self.row_entry.delete(1)
        """
        self.column_entry = CustomSizeEntryFrame(self, "Anzahl an Spalten:",
                                                 40, self.columns, "9")
        self.row_entry = CustomSizeEntryFrame(self, "Anzahl an Reihen:",
                                              40, self.rows, "6")

        self.column_entry.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.row_entry.grid(row=0, column=1, padx=10, pady=10, sticky="e")

    def get(self):
        columns = self.columns.get()
        rows = self.rows.get()
        return columns, rows


class SizeButtonFrame(ctk.CTkFrame):
    def __init__(self, master, options):
        super().__init__(master)
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.options = options
        self.radio_buttons = []
        self.checked = ctk.StringVar()

        for i, value in enumerate(self.options):
            radiobutton = ctk.CTkRadioButton(self, text=value, value=value,
                                             variable=self.checked, command=master.check_size_radiobutton)
            radiobutton.grid(row=0, column=i, padx=(40, 0), pady=10, sticky="ew")
            self.radio_buttons.append(radiobutton)
        self.radio_buttons[1].select()

    def get(self):
        return self.checked.get()


class ChestGenerator:
    def __init__(self, item="dirt", columns=9, rows=6, scale=1):
        # Liste mit unstackable Items
        self.non_stackable_items = ["bundle",
                                    "_bucket",
                                    "boat",
                                    "sword",
                                    "pickaxe",
                                    "axe",
                                    "hoe",
                                    "shovel",
                                    "helmet",
                                    "chestplate",
                                    "leggings",
                                    "boots",
                                    "bow",
                                    "cake",
                                    "elytra",
                                    "flint_and_steel",
                                    "fishing_rod",
                                    "minecart",
                                    "music_disc",
                                    "writable_book",
                                    "trident",
                                    "totem_of_undying",
                                    "potion",
                                    "enchanted"]

        self.count_16 = Image.open("res/count16.png").convert("RGBA")
        self.count_64 = Image.open("res/count64.png").convert("RGBA")

        self.scale = scale
        self.columns = columns
        self.rows = rows

        self.set_item(item)
        self.stackable = True
        self.set_count_image()

    def check_stackable(self):
        stackable = True
        for item in self.non_stackable_items:
            if item in self.item_url and "bowl" not in self.item_url:
                stackable = False
        self.stackable = stackable

    def set_item(self, item):
        self.item_url, self.item_img = self.get_item(item)
        self.check_stackable()

    def get_item(self, item):
        if " " in item:
            item_url = item.replace(" ", "_").lower()  # Leerzeichen mit Unterstrich ersetzen
        else:
            item_url = item.lower()

        try:
            item_img = Image.open(f"res/items/{item_url}.png")  # versuchen, das Bild des Items zu laden
        except FileNotFoundError:
            raise FileNotFoundError(f"{item} ist kein item in minecraft oder du hast dich verschrieben.")
        return item_url, item_img.convert("RGBA")

    def set_count_image(self):
        if (self.item_url == "ender_pearl" or "sign" in self.item_url or "egg" == self.item_url
                or "honey_bottle" in self.item_url or "bucket" in self.item_url and "bowl" not in self.item_url):
            self.count_img = self.count_16  # wenn ein Stack 16 ist
        else:
            self.count_img = self.count_64  # wenn ein Stack 64 ist

    def set_scale(self, scale):
        self.scale = int(scale)

    def resize_chest_interface(self, columns, rows, original, chest_img):
        expand_chest = self.generate_expanded_chest("w", columns, original, chest_img)
        expand_chest = self.generate_expanded_chest("h", rows, original, expand_chest)
        return expand_chest

    def generate_expanded_chest(self, direction, expand_amount, original, chest_img):
        offset = 30 if original else 0
        # Kiste in die Breite erweitern
        if direction == "w":
            chest_column = chest_img.crop((chest_img.width - 75, 0, chest_img.width - 21, chest_img.height))
            chest_title = chest_img.crop((0, 0, chest_img.width - 423, 21 + offset))
            chest_border_left = chest_img.crop((0, 0, 21, chest_img.height))
            chest_border_right = chest_img.crop((chest_img.width - 21, 0, chest_img.width, chest_img.height))
            new_chest_img = Image.new("RGBA", (chest_border_left.width + chest_column.width * expand_amount +
                                               chest_border_right.width, chest_img.height))
            new_chest_img.paste(chest_border_left)
            for x in range(expand_amount):
                new_chest_img.paste(chest_column, (x * chest_column.width + chest_border_left.width, 0))
            new_chest_img.paste(chest_border_right, (new_chest_img.width - chest_border_right.width, 0))
            new_chest_img.paste(chest_title)
        # Kiste in die Höhe erweitern
        elif direction == "h":
            chest_row = chest_img.crop((0, chest_img.height - 75, chest_img.width, chest_img.height - 21))
            chest_border_upper = chest_img.crop((0, 0, chest_img.width, 21 + offset))
            chest_border_lower = chest_img.crop((0, chest_img.height - 21, chest_img.width, chest_img.height))
            new_chest_img = Image.new("RGBA", (chest_img.width, chest_border_upper.height +
                                               chest_row.height * expand_amount + chest_border_lower.height))
            new_chest_img.paste(chest_border_upper)
            for y in range(expand_amount):
                new_chest_img.paste(chest_row, (0, y * chest_row.height + chest_border_upper.height))
            new_chest_img.paste(chest_border_lower, (0, new_chest_img.height - chest_border_lower.height))
        else:
            raise ValueError("direction can only be 'w' or 'h'")
        return new_chest_img

    def generate_chest_image(self, original):
        height_offset = 54 if original else 24
        if self.columns == 9 and self.rows == 6:
            path = "res/chest_big_original.png" if original else "res/chest_big.png"
            chest_img = Image.open(path).convert("RGBA")
            chest_img = self.add_item_to_chest(chest_img, self.item_img, self.count_img, height_offset, self.rows)
        elif self.columns == 9 and self.rows == 3:
            path = "res/chest_small_original.png" if original else "res/chest_small.png"
            chest_img = Image.open(path).convert("RGBA")
            chest_img = self.add_item_to_chest(chest_img, self.item_img, self.count_img, height_offset, self.rows)
        else:
            if original:
                if self.columns < 2:
                    raise ValueError("chest menu must be at least 2 wide to be original")
                else:
                    path = "res/chest_small_original.png"
            else:
                path = "res/chest_small.png"
            chest_img = Image.open(path).convert("RGBA")
            chest_img = self.add_item_to_chest(chest_img, self.item_img, self.count_img, height_offset, 3)
            chest_img = self.resize_chest_interface(self.columns, self.rows, original, chest_img)

        chest_img = self.scale_image(chest_img)

        return chest_img

    def add_item_to_chest(self, chest_img, item_img, count_img, height_offset, rows):
        for y in range(rows):
            for x in range(9):
                chest_img.paste(item_img, (x * 54 + 24, y * 54 + height_offset), item_img)
                if self.stackable:
                    chest_img.paste(count_img, (x * 54 + 24, y * 54 + height_offset), count_img)
        return chest_img

    def scale_image(self, image):
        width, height = image.size
        output_img = image.resize((width * self.scale, height * self.scale),
                                  resample=Image.Resampling.NEAREST)
        return output_img


class ChestMenuGen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("500x600")
        self.title("Chest Menu Generator")
        self._set_appearance_mode("dark")
        self.grid_columnconfigure((0, 1), weight=1)

        self.items = self.load_item_list()

        self.chest_gen = ChestGenerator()

        # widgets hinzufügen
        self.headline = ctk.CTkLabel(self, text="Chest Menu Generator", font=("arial", 20))
        self.headline.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="n", columnspan=2)

        self.dropdown_headline = ctk.CTkLabel(self, text="Item auswählen:")
        self.dropdown_headline.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="n", columnspan=2)
        self.item = ctk.StringVar()
        self.dropdown = SearchCombobox(self, self.items, variable=self.item)
        self.dropdown.grid(row=2, column=0, padx=(0, 20), pady=(0, 20), sticky="n", columnspan=2)

        self.size_radiobutton_frame = SizeButtonFrame(self, ["Single Chest", "Double Chest", "Custom"])
        self.size_radiobutton_frame.grid(row=3, column=0, padx=20, pady=20, sticky="nesw", columnspan=2)

        self.custom_size_frame = CustomSizeFrame(self)

        self.use_original = ctk.BooleanVar()
        self.original_switch = ctk.CTkSwitch(self, text="Originale Kisten-Überschrift verwenden",
                                             variable=self.use_original)
        self.original_switch.grid(row=5, column=0, padx=20, pady=20, sticky="n", columnspan=2)

        self.scale = ctk.DoubleVar(value=1.0)
        self.min_scale_label = ctk.CTkLabel(self, text="1")
        self.min_scale_label.grid(row=6, column=0, padx=(135, 0), pady=(5, 0), sticky="w", columnspan=2)
        self.max_scale_label = ctk.CTkLabel(self, text="20")
        self.max_scale_label.grid(row=6, column=0, padx=(0, 135), pady=(5, 0), sticky="e", columnspan=2)
        self.scale_slider = ctk.CTkSlider(self, from_=1, to=20, number_of_steps=38, variable=self.scale)
        self.scale_slider.grid(row=6, column=0, padx=20, pady=(11, 0), sticky="n", columnspan=2)
        self.scale_label = ctk.CTkLabel(self, text="Scale: ")
        self.scale_label.grid(row=7, column=0, padx=(175, 0), pady=10, sticky="w")
        self.scale_entry = ctk.CTkEntry(self, textvariable=self.scale, width=45)
        self.scale_entry.grid(row=7, column=1, padx=(0, 175), pady=10, sticky="e")

        self.submit = ctk.CTkButton(self, text="Generate Chest Menu", font=("arial", 20),
                                    corner_radius=6, command=self.generate)
        self.submit.place(relx=0.5, rely=0.9, anchor="s")

        self.success_message = ctk.CTkLabel(self, text="Menü erfolgreich generiert", font=("Arial", 20),
                                            text_color="#004D13", fg_color="#38C900", corner_radius=5)
        self.bind("<Button-1>", self.hide_success_message)

    def generate(self, choice=""):
        if self.size_radiobutton_frame.get() == "Single Chest":
            self.chest_gen.columns = 9
            self.chest_gen.rows = 3
        elif self.size_radiobutton_frame.get() == "Double Chest":
            self.chest_gen.columns = 9
            self.chest_gen.rows = 6
        else:
            self.chest_gen.columns = self.custom_size_frame.get()[0]
            self.chest_gen.rows = self.custom_size_frame.get()[1]

        self.chest_gen.set_item(self.item.get())
        self.chest_gen.set_count_image()
        # if self.use_scale.get():
        # if self.use_scale.get():
        self.chest_gen.set_scale(self.scale.get())
        self.chest_gen.generate_chest_image(self.use_original.get()).save("chest.png", format="png")

        self.after(50, lambda: self.success_message.place(relx=0.5, rely=0.98, anchor="s"))

    def hide_success_message(self, event):
        self.success_message.grid_forget()

    def check_size_radiobutton(self):
        if self.size_radiobutton_frame.get() == "Custom":
            self.custom_size_frame.grid(row=4, column=0, padx=20, pady=0, sticky="ew", columnspan=2)
        else:
            self.custom_size_frame.grid_forget()

    def load_item_list(self):
        item_list = os.listdir("res/items")
        new_item_list = []
        for item in item_list:
            item = item.removesuffix(".png")
            if "_" in item:
                item = item.replace("_", " ")
            new_item_list.append(item.title())
        return new_item_list

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    ChestMenuGen().start()
