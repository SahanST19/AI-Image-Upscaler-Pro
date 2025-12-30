import customtkinter as ctk
import os
import cv2
import torch
import threading
from tkinter import filedialog
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import warnings
import webbrowser

warnings.filterwarnings("ignore")

# --- Default Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UpscalerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Pro AI Upscaler - Photos v2.0")
        self.geometry("950x750")
        self.resizable(True, True)

        # Variables
        self.selected_files = []
        self.input_mode = "NONE" 
        self.custom_output_folder = None 

        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # --- Top Bar (Theme Switch & Title) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        # Theme Switch
        self.switch_var = ctk.StringVar(value="on")
        self.switch_theme = ctk.CTkSwitch(self.header_frame, text="Dark Mode", command=self.toggle_theme, 
                                          variable=self.switch_var, onvalue="on", offvalue="off")
        self.switch_theme.pack(side="left")

        # Title
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="AI IMAGE ENHANCER", font=("Roboto Medium", 26), text_color="#3B8ED0")
        self.lbl_title.pack(side="top")
        self.lbl_subtitle = ctk.CTkLabel(self.header_frame, text="High-Fidelity x4 Upscaling (Stable Mode)", font=("Roboto", 12), text_color="gray")
        self.lbl_subtitle.pack(side="top")

        # --- Input Selection ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self.input_frame, text="STEP 1: Select Images", font=("Arial", 12, "bold")).pack(pady=5)
        self.btn_files = ctk.CTkButton(self.input_frame, text="📂 Select Specific Photos", command=self.select_files, width=200, height=35)
        self.btn_files.pack(side="left", padx=20, pady=10, expand=True)
        self.btn_folder = ctk.CTkButton(self.input_frame, text="📁 Select Input Folder", command=self.select_folder, width=200, height=35)
        self.btn_folder.pack(side="right", padx=20, pady=10, expand=True)
        self.lbl_selection = ctk.CTkLabel(self, text="No images selected", text_color="#FF9800")
        self.lbl_selection.grid(row=2, column=0, pady=5)

        # --- Output Selection ---
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self.output_frame, text="STEP 2: Where to Save? (Optional)", font=("Arial", 12, "bold")).pack(pady=5)
        self.btn_output = ctk.CTkButton(self.output_frame, text="💾 Select Save Location", command=self.select_output_folder, width=250, height=35, fg_color="#5E35B1", hover_color="#4527A0")
        self.btn_output.pack(pady=5)
        self.lbl_output_path = ctk.CTkLabel(self.output_frame, text="Default: New folder inside input location", text_color="gray", font=("Consolas", 11))
        self.lbl_output_path.pack(pady=5)

        # --- Hardware Status ---
        self.device_label = ctk.CTkLabel(self, text="System Check...", font=("Consolas", 12))
        self.device_label.grid(row=4, column=0, pady=5)
        self.check_hardware()

        # --- Progress Bar ---
        self.progress_bar = ctk.CTkProgressBar(self, width=600, height=15)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=5, column=0, pady=10, sticky="ew", padx=50)

        # --- Log Box ---
        self.log_box = ctk.CTkTextbox(self, height=150, font=("Consolas", 12))
        self.log_box.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        self.log("Ready. Use the switch top-left to change theme.")

        # --- Start Button & Footer ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=7, column=0, pady=20, sticky="ew")
        self.btn_start = ctk.CTkButton(self.bottom_frame, text="START PROCESSING", command=self.start_thread, width=300, height=50, font=("Roboto", 16, "bold"), fg_color="#00C853", hover_color="#009624")
        self.btn_start.pack()
        
        # Clickable Footer for GitHub
        self.footer = ctk.CTkLabel(self.bottom_frame, text="Developed by Sahan Tharuka © 2025 (Visit GitHub)", font=("Arial", 11), text_color="#555555", cursor="hand2")
        self.footer.pack(pady=(10, 0))
        self.footer.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/SahanST19"))

    def toggle_theme(self):
        if self.switch_var.get() == "on":
            ctk.set_appearance_mode("Dark")
            self.switch_theme.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("Light")
            self.switch_theme.configure(text="Light Mode")

    def check_hardware(self):
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            self.device_label.configure(text=f"🚀 GPU ACTIVE: {gpu_name}", text_color="#00E676" if self.switch_var.get()=="on" else "#007E33")
            self.device = torch.device('cuda')
        else:
            self.device_label.configure(text="⚠️ GPU NOT FOUND: Using CPU (Slower)", text_color="#FF3D00")
            self.device = torch.device('cpu')

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.webp")])
        if files:
            self.selected_files = list(files)
            self.input_mode = "FILES"
            self.lbl_selection.configure(text=f"✅ {len(files)} Images Selected", text_color="#00E676")
            self.log(f"Selected {len(files)} individual files.")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_mode = "FOLDER"
            self.selected_folder = folder
            count = len([f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
            self.lbl_selection.configure(text=f"✅ Folder Selected ({count} images found)", text_color="#00E676")
            self.log(f"Selected input folder: {folder}")

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.custom_output_folder = folder
            self.lbl_output_path.configure(text=f"Save to: {folder}", text_color="#00E676")
            self.log(f"Custom output folder set: {folder}")

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")

    def start_thread(self):
        if self.input_mode == "NONE":
            self.log("❌ Error: Please select photos first!")
            return
        self.btn_start.configure(state="disabled", text="Processing...")
        threading.Thread(target=self.process_images).start()

    def process_images(self):
        try:
            images_to_process = []
            output_dir = ""

            if self.input_mode == "FILES":
                images_to_process = self.selected_files
                if self.custom_output_folder: output_dir = self.custom_output_folder
                else: output_dir = os.path.join(os.path.dirname(self.selected_files[0]), "Upscaled_Output")
            elif self.input_mode == "FOLDER":
                base_dir = self.selected_folder
                files = [f for f in os.listdir(base_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                images_to_process = [os.path.join(base_dir, f) for f in files]
                if self.custom_output_folder: output_dir = self.custom_output_folder
                else: output_dir = os.path.join(base_dir, "Upscaled_Output")

            if not images_to_process:
                self.log("No images found to process.")
                self.btn_start.configure(state="normal", text="START PROCESSING")
                return

            os.makedirs(output_dir, exist_ok=True)
            
            self.log(f"Loading AI Model on {self.device} (Tiling Enabled)...")
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            model_url = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
            
            upscaler = RealESRGANer(
                scale=4, model_path=model_url, model=model, 
                tile=512, tile_pad=10, pre_pad=0,
                half=False, device=self.device
            )

            total = len(images_to_process)
            self.log(f"Starting Batch Process: {total} Images")
            self.log(f"Saving to: {output_dir}")

            for i, img_path in enumerate(images_to_process):
                img_name = os.path.basename(img_path)
                self.log(f"Upscaling ({i+1}/{total}): {img_name}...")
                progress = (i + 1) / total
                self.progress_bar.set(progress)

                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    output, _ = upscaler.enhance(img, outscale=4)
                    save_name = f"{os.path.splitext(img_name)[0]}_x4.jpg"
                    save_path = os.path.join(output_dir, save_name)
                    cv2.imwrite(save_path, output)
                else:
                    self.log(f"Skipped invalid file: {img_name}")

            self.log("✅ All Tasks Completed Successfully!")
            self.progress_bar.set(1)

        except Exception as e:
            self.log(f"❌ Critical Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.btn_start.configure(state="normal", text="START PROCESSING")

if __name__ == "__main__":
    app = UpscalerApp()
    app.mainloop()