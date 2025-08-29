import base64
import io
import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        self.geometry('600x400')
        self.title("Chat Client")

        self.username = "Artem"

        # Меню
        self.menu_frame = CTkFrame(self, width=30, height=400)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False
        self.speed_animate_menu = -20

        self.btn = CTkButton(self, text=">", command=self.toggle_show_menu, width=30, height=30)
        self.btn.place(x=0, y=0)

        # Основне поле чату
        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=30, y=0)

        # Поле введення та кнопки
        self.message_entry = CTkEntry(self, placeholder_text="Введіть повідомлення:", height=40)
        self.message_entry.place(x=30, y=360)

        self.send_button = CTkButton(self, text="➤", width=50, height=40, command=self.send_message)
        self.send_button.place(x=520, y=360)

        self.open_img_button = CTkButton(self, text="🖼", width=50, height=40, command=self.open_image)
        self.open_img_button.place(x=460, y=360)

        # Елементи меню (спочатку приховані)
        self.label = None
        self.entry = None
        self.save_button = None

        self.adaptive_ui()

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            hello = f"[TEXT]{self.username}[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

    def toggle_show_menu(self):
        if self.is_show_menu:
            # Ховаємо меню
            self.is_show_menu = False
            self.speed_animate_menu = -20
            self.btn.configure(text='>')
            # Видаляємо елементи меню, якщо вони є
            if self.label:
                self.label.destroy()
                self.label = None
            if self.entry:
                self.entry.destroy()
                self.entry = None
            if self.save_button:
                self.save_button.destroy()
                self.save_button = None
        else:
            # Показуємо меню
            self.is_show_menu = True
            self.speed_animate_menu = 20
            self.btn.configure(text='<')
            # Додаємо елементи меню
            if not self.label:
                self.label = CTkLabel(self.menu_frame, text="Ім'я")
                self.label.pack(pady=30)
            if not self.entry:
                self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
                self.entry.pack(pady=10)
            if not self.save_button:
                self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
                self.save_button.pack(pady=10)
        self.animate_menu()

    def animate_menu(self):
        new_width = self.menu_frame.winfo_width() + self.speed_animate_menu
        if self.is_show_menu:
            if new_width >= 200:
                new_width = 200
            else:
                self.menu_frame.configure(width=new_width)
                self.after(10, self.animate_menu)
                return
        else:
            if new_width <= 30:
                new_width = 30
            else:
                self.menu_frame.configure(width=new_width)
                self.after(10, self.animate_menu)
                return

        self.menu_frame.configure(width=new_width)

    def save_name(self):
        if self.entry:
            new_name = self.entry.get().strip()
            if new_name:
                self.username = new_name
                self.add_message(f"Ваш новий нік: {self.username}")

    def adaptive_ui(self):
        # Оновлюємо розміри та позиції елементів при зміні вікна
        self.menu_frame.configure(height=self.winfo_height())

        menu_width = self.menu_frame.winfo_width()
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        self.chat_field.place(x=menu_width, y=0)
        self.chat_field.configure(width=window_width - menu_width, height=window_height - 50)

        self.message_entry.place(x=menu_width + 10, y=window_height - 45)
        self.message_entry.configure(width=window_width - menu_width - 130)

        self.open_img_button.place(x=window_width - 110, y=window_height - 50)
        self.send_button.place(x=window_width - 55, y=window_height - 50)

        self.after(100, self.adaptive_ui)

    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color='#444444', corner_radius=5)
        message_frame.pack(pady=5, anchor='w', padx=10)

        wrap_length = self.winfo_width() - self.menu_frame.winfo_width() - 60

        if img is None:
            CTkLabel(message_frame, text=message, wraplength=wrap_length,
                     text_color='white', justify='left').pack(padx=10, pady=5)
        else:
            CTkLabel(message_frame, text=message, wraplength=wrap_length,
                     text_color='white', image=img, compound='top',
                     justify='left').pack(padx=10, pady=5)

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                pass
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]
                try:
                    img_data = base64.b64decode(b64_img)
                    pil_img = Image.open(io.BytesIO(img_data))
                    ctk_img = CTkImage(pil_img, size=(300, 300))
                    self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
                except Exception as e:
                    self.add_message(f"Помилка відображення зображення: {e}")
            else:
                self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())
            img = CTkImage(light_image=Image.open(file_name), size=(300, 300))
            self.add_message('', img)
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
