import tkinter as tk
import os
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import numpy as np
import tifffile as tif
import time  # Simule un traitement long
import SimpleITK as sitk

class ImageProcessingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Registration (Translation) App")

        # Variables
        self.image_path = None
        self.image_read = None
        self.image_array = None
        self.num_channels = 0
        self.selected_channel = tk.IntVar(value=-1)

        # UI Elements
        self.setup_ui()

    def setup_ui(self):
        # Frame pour charger une image
        load_frame = tk.Frame(self.root)
        load_frame.pack(pady=10)

        tk.Button(load_frame, text="Browse Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        self.image_label = tk.Label(load_frame, text="No image loaded")
        self.image_label.pack(side=tk.LEFT)

        # Menu déroulant pour sélectionner un canal
        channel_frame = tk.Frame(self.root)
        channel_frame.pack(pady=10)
        tk.Label(channel_frame, text="Choose channel for treatment:").pack(side=tk.LEFT, padx=5)
        self.channel_menu = ttk.Combobox(self.root, textvariable=self.selected_channel, state="disabled")
        self.channel_menu.pack(pady=10)

        # Bouton pour commencer le traitement
        self.process_button = tk.Button(self.root, text="Process Channel", command=self.process_channel, state="disabled")
        self.process_button.pack(pady=10)

        # Barre de progression
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)
        
        message_frame = tk.Frame(self.root)
        message_frame.pack(pady=10)

        tk.Label(message_frame, text="This code uses SimpleITK Registration function to find the 3D drift \non one channel (the applied to all others) for each time point \naccording to the first one",font=("Helvetica", 10, "italic")).pack(side=tk.LEFT, padx=5)

    def reset_ui(self):
        # Réinitialiser le menu déroulant
        self.channel_menu["values"] = []
        self.channel_menu["state"] = "disabled"
        self.selected_channel.set(-1)

        # Réinitialiser la barre de progression
        self.progress["value"] = 0

        # Désactiver le bouton de traitement
        self.process_button["state"] = "disabled"

        # Réinitialiser le texte de l'étiquette
        self.image_label.config(text="No image loaded")

    def load_image(self):
        self.reset_ui()    	
        # Ouvrir une boîte de dialogue pour sélectionner une image
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.tif;*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        self.image_path = file_path

        self.image_read = tif.imread(self.image_path)  # Dimensions : (T, C, Z, X, Y)
        self.image_data = self.image_read.astype(np.float32)  # Conversion des données
        self.image_array = np.array(self.image_read)
        print(self.image_array.shape)
        # Vérifier les dimensions de l'image
        if len(self.image_array.shape) < 3:
            messagebox.showerror("Error", "The image must have multiple channels.")
            return

        self.num_channels = self.image_array.shape[2]

        # Mettre à jour le menu des canaux
        self.channel_menu["values"] = [str(i+1) for i in range(self.num_channels)]
        self.channel_menu["state"] = "readonly"
        self.selected_channel.set(1)

        # Activer le bouton de traitement
        self.process_button["state"] = "normal"

        self.image_label.config(text=f"Loaded: {self.image_path.split('/')[-1]} ({self.num_channels} channels)")
        self.dossier, nom_fichier = os.path.split(self.image_path)
        self.nom_sans_ext, self.ext = os.path.splitext(nom_fichier)

    def process_channel(self):

        channel = self.selected_channel.get()-1
        if channel < 0 or channel >= self.num_channels:
            messagebox.showerror("Error", "Please select a valid channel.")
            return

        # Préparer le traitement
        num_frames = self.image_array.shape[0]  # Simuler 10 frames à traiter
        self.progress["maximum"] = num_frames
        
        image = self.image_read[:, :, channel, :, :]  # Dimensions : (T, Z, X, Y)
        print("Dimensions du sous-ensemble sélectionné :", image.shape)
        
        fixed_image = sitk.GetImageFromArray(image[0])  # Image fixe : premier point temporel
        print(fixed_image.GetSize())
        fixed_image = sitk.Cast(fixed_image, sitk.sitkFloat32)  # Conversion en float32
        print(fixed_image.GetSize())
        # Configuration de la registration
        registration = sitk.ImageRegistrationMethod()
        registration.SetMetricAsMeanSquares()  # Utilisation de la métrique des moindres carrés
        registration.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0,minStep=1e-6,numberOfIterations=200)
        registration.SetInterpolator(sitk.sitkLinear)
        registration.SetInitialTransform(sitk.TranslationTransform(fixed_image.GetDimension()))
        transformed_data = np.zeros_like(self.image_read)
        num_frames = 10
        
        for channel in range(self.num_channels):
        	transformed_data[0, :, channel, :, :] = self.image_data[0, :, channel, :, :]

		
        for t in range(1, num_frames):
            self.root.update_idletasks()
            moving_image = sitk.GetImageFromArray(image[t])  # Image en mouvement
            moving_image = sitk.Cast(moving_image, sitk.sitkFloat32)
            
            # Effectuer la registration
            print(f"Registration du point temporel {t}...")
            # Calculer la transformation pour ce frame
            transform = registration.Execute(fixed_image, moving_image)
            print(transform)
            # Appliquer la transformation à tous les canaux pour ce frame
            for channel in range(self.num_channels):
            	# Convertir le canal en SimpleITK
            	moving_channel_image = sitk.GetImageFromArray(self.image_data[t, :, channel, :, :])
            	# Resampler l'image avec la transformation
            	resampler = sitk.ResampleImageFilter()
            	resampler.SetReferenceImage(fixed_image)  # Référence pour la taille/dimension
            	resampler.SetTransform(transform)
            	resampler.SetInterpolator(sitk.sitkLinear)
            	# Appliquer la transformation
            	transformed_channel_image = resampler.Execute(moving_channel_image)
            	print(transformed_channel_image.GetSize())
            	# Stocker le résultat dans le tableau final
            	transformed_data[t, :, channel, :, :] = sitk.GetArrayFromImage(transformed_channel_image)
            	print(transformed_data[t, :, channel, :, :].shape)

            # Mise à jour de la progression
            self.progress["value"] = t-1

        nom_fichier_tr = f"{self.nom_sans_ext}_registered_3Dtrans_chan{self.selected_channel.get()}_8b_{self.ext}"		
        output_path = os.path.join(self.dossier, nom_fichier_tr)
        messagebox.showinfo("Info", f"Processing completed, file saved in {output_path}")
        tif.imwrite(output_path, transformed_data.astype(np.uint8), imagej=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()
