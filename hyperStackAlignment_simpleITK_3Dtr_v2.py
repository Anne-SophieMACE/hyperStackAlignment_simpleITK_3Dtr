import tkinter as tk
import os
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import numpy as np
import tifffile as tif
import time  # Simule un traitement long
import SimpleITK as sitk
import psutil
import subprocess
import numpy as np
import csv
import sys

# v3: saves transfo

class ImageProcessingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Registration (Translation) App")

        # Variables
        self.folder_path = ""
        self.factor = 1
        self.selected_channel = -1
        # UI Elements
        self.setup_ui()
    # reads X Y Z spacing
    def spacing_ZYX(self,file_path):
    	with tif.TiffFile(file_path) as tifImg:
    		page = tifImg.pages[0]
    		tags = page.tags
    		metadata = tifImg.imagej_metadata
			
    		x_res = tags.get('XResolution')
    		x_voxel_size = 1 / x_res.value[0] * x_res.value[1]
    		y_res = tags.get('YResolution')
    		y_voxel_size = 1 / y_res.value[0] * y_res.value[1]
    		z_voxel_size = metadata['spacing']
			
    		timeStep = metadata['finterval']
    		
    		metadata = tifImg.imagej_metadata
			
    	return (z_voxel_size,y_voxel_size,x_voxel_size,metadata)

    # Preparation of the interface
    def setup_ui(self):
        load_frame = tk.Frame(self.root)
        load_frame.pack(pady=10)

        tk.Button(load_frame, text="Browse Folder", command=self.load_folder).pack(side=tk.LEFT, padx=5)
        self.image_label = tk.Label(load_frame, text="No folder selected")
        self.image_label.pack(side=tk.LEFT)
        message_frame = tk.Frame(self.root)
        message_frame.pack(pady=10)
        tk.Label(message_frame, text="All tif files of the selected folder will be treated",font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)


        # Channel selection
        channel_frame = tk.Frame(self.root)
        channel_frame.pack(pady=10)
        tk.Label(channel_frame, text="Channel index (starting at 1):").pack(side=tk.LEFT, padx=5)
        self.channel_var = tk.IntVar(value=-1)
        self.channel_entry = tk.Entry(channel_frame, textvariable=self.channel_var, width=5)
        self.channel_entry.pack(side=tk.LEFT)

        
        factor_frame = tk.Frame(self.root)
        factor_frame.pack(pady=10)
        tk.Label(factor_frame, text="Subsampling (XY) factor:").pack(side=tk.LEFT, padx=5)
        self.factor_var = tk.IntVar(value=1)  # valeur par défaut
        self.factor_entry = tk.Entry(factor_frame, textvariable=self.factor_var, width=5)
        self.factor_entry.pack(side=tk.LEFT)

        self.process_button = tk.Button(self.root, text="Process Folder", command=self.process_channel, state="disabled")
        self.process_button.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)
        
        message_frame = tk.Frame(self.root)
        message_frame.pack(pady=10)
        tk.Label(message_frame, text="This code uses SimpleITK Registration function to find the 3D drift \non one channel (the applied to all others) for each time point \naccording to the first one",font=("Helvetica", 10, "italic")).pack(side=tk.LEFT, padx=5)

    def reset_ui(self):
        self.channel_var.set(-1)
        self.factor_var.set(2)

        self.progress["value"] = 0

        self.process_button["state"] = "disabled"
        self.image_label.config(text="No folder selected")


    def resource_path(self,relative_path):
    	if hasattr(sys, '_MEIPASS'):
    		base_path = os.path.dirname(sys.executable)
    	else:
    		base_path = os.path.dirname(os.path.abspath(__file__))
    	return os.path.join(base_path, relative_path)


    def get_transformed_bounding_box(self,image, transform):
    	size = image.GetSize()
    	spacing = image.GetSpacing()
    	origin = image.GetOrigin()
    	# Calculer les coins extrêmes
    	corners = []
    	for z in [0, size[0]-1]:
    		for y in [0, size[1]-1]:
    			for x in [0, size[2]-1]:
    				index = (z, y, x)
    				physical_point = image.TransformIndexToPhysicalPoint(index)
    				transformed_point = transform.TransformPoint(physical_point)
    				corners.append(transformed_point)
    	min_corner = [min(p[i] for p in corners) for i in range(3)]
    	max_corner = [max(p[i] for p in corners) for i in range(3)]
    	
    	return min_corner, max_corner

    def create_fiji_csv(self,output_csv_path, t, c, z):
    	with open(output_csv_path, 'w', newline='') as csvfile:
    		writer = csv.writer(csvfile)
    		writer.writerow(['T', 'C', 'Z'])
    		writer.writerow([t, c, z])
	                    
    def load_folder(self):
    	self.reset_ui()
    	folder = filedialog.askdirectory()
    	if not folder:
    		returnself.channel_menu["state"] = "disabled"
	
    	self.folder_path = folder
    	self.image_label.config(text=f"Folder selected: {folder.split('/')[-1]}")
    	self.process_button["state"] = "normal"
    		
    def process_channel(self):
        config_path = self.resource_path("config_FijiPath.txt")
        print(config_path)
        chosenChannel = self.channel_var.get() - 1
        
        ext = ".tif"
        files = sorted([f for f in os.listdir(self.folder_path) if f.endswith(ext)])
        
        if len(files) == 0:
        	messagebox.showerror("Error", f"No files with extension {ext} found in folder.")
        	return
        
        file_paths = [os.path.join(self.folder_path, f) for f in files]        
        self.factor = self.factor_var.get()

        
        for  i, image_path in enumerate(file_paths, start=1):
        	print(f"Image {i} / {len(file_paths)}")
        	z, y, x, metadata = self.spacing_ZYX(image_path)
        	
        	image_read = tif.memmap(image_path)#tif.imread(image_path)  # Dimensions : (T, C, Z, X, Y)
        	image_array = np.array(image_read)
        	
        	num_frames = image_array.shape[0] 
        	num_channels = image_array.shape[2]
        	if chosenChannel < 0 or chosenChannel >= num_channels:
        		print(f"Skipping file {image_path}: chosen channel {chosenChannel+1} not available (num_channels={num_channels})")
        		continue  # passe au fichier suivant
        	
        	sizeXYZ = [image_array.shape[4], image_array.shape[3],image_array.shape[1]]
        	self.progress["maximum"] = num_frames
        	
	        basename = os.path.splitext(os.path.basename(image_path))[0]
	        output_dir = os.path.join(os.path.dirname(image_path), basename + "_trFrames_chan"+str(chosenChannel+1)+"_subSamp"+str(self.factor))
	        os.makedirs(output_dir, exist_ok=True)
	        
	        # image = image_read[:, :, channel, :, :]  # Dimensions : (T, Z, C, X, Y)
	        fixed_image = sitk.GetImageFromArray(image_read[0, :, chosenChannel, :, :])
	        fixed_image = sitk.Cast(fixed_image, sitk.sitkFloat32)
	        
	        # Configuration de la registration
	        registration = sitk.ImageRegistrationMethod()
	        registration.SetMetricAsMeanSquares()  # Utilisation de la métrique des moindres carrés
	        registration.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0,minStep=1e-6,numberOfIterations=200)
	        registration.SetInterpolator(sitk.sitkLinear)
	        registration.SetInitialTransform(sitk.TranslationTransform(fixed_image.GetDimension()))
			
	        transforms = []
	        offsets_tr = []
	        all_max_pts = []
	        
	        transfos_path = os.path.join(output_dir, "transfos.npy")
	        start_frame = 1
	        if os.path.exists(transfos_path):
	        	print("Existing transforms found, resuming...")
	        	offsets_tr = list(np.load(transfos_path))
	        	
	        	transforms = []
	        	for off in offsets_tr[1:]:
	        		tr = sitk.TranslationTransform(3)
	        		tr.SetOffset(tuple(float(x) for x in off))

	        		transforms.append(tr)
	        	
	        	start_frame = len(offsets_tr)
	        	print(f"Resuming from frame t = {start_frame}")
	        else:
		        offsets_tr.append([0.0,0.0,0.0])
		    
	        for t in range(start_frame, num_frames):
	            self.root.update_idletasks()
	            moving_image = sitk.GetImageFromArray(image_read[t, :, chosenChannel, :, :])  # Image en mouvement
	            moving_image = sitk.Cast(moving_image, sitk.sitkFloat32)
	            
	            # Effectuer la registration
	            print(f"Computing transformation for temporal point  {t}...")
	            # Calculer la transformation pour ce frame
	            transform = registration.Execute(fixed_image, moving_image)
	            offset = transform.GetOffset()
	            transform_copy = sitk.TranslationTransform(3)  # 3D
	            transform_copy.SetOffset(offset)
	            transforms.append(transform_copy)
	            offsets_tr.append(transform.GetOffset())
	            np.save(os.path.join(output_dir, "transfos.npy"), np.array(offsets_tr, dtype=np.float64))

			
	        global_min = np.floor([min(pts[i] for pts in offsets_tr) for i in range(3)])
	        global_max = np.ceil([max(pts[i] for pts in offsets_tr) for i in range(3)])
	        #print( type(transforms))
	        #print(transforms)
	        global_origin = global_min
	        spacing = fixed_image.GetSpacing()
	        global_size = [int(np.ceil((global_max[i] - global_min[i]) / spacing[i]))+sizeXYZ[i]+1 for i in range(3)]
	        #transformed_data = np.zeros((num_frames,  global_size[2], self.num_channels, global_size[1], global_size[0]), dtype=np.uint8)
	
	                
	        for t in range(0, num_frames):
	        	print(f"Registration temporal point  {t}...")
	        	for channel in range(num_channels):
	        		moving_channel_image = sitk.GetImageFromArray(image_read[t, :, channel, :, :])
	        		moving_channel_image = sitk.Cast(moving_channel_image, sitk.sitkFloat32)
	        		moving_image_pad = np.zeros([global_size[2], global_size[1],global_size[0]])
	        		moving_image_pad[int(global_max[2]):int(global_max[2]+sizeXYZ[2]),int(global_max[1]):int(global_max[1]+sizeXYZ[1]),int(global_max[0]):int(global_max[0]+sizeXYZ[0])] = sitk.GetArrayFromImage(moving_channel_image)
	        		if( t == 0 ):
	        			transformed_channel_image = sitk.GetImageFromArray(moving_image_pad)
	        		else:
	        			transform = transforms[t-1]
		        		moving_image_pad = sitk.GetImageFromArray(moving_image_pad)
		        		resampler = sitk.ResampleImageFilter()
		        		resampler.SetReferenceImage(moving_image_pad)  # Référence pour la taille/dimension
		        		resampler.SetTransform(transform)
		        		resampler.SetInterpolator(sitk.sitkLinear)
		        		transformed_channel_image = resampler.Execute(moving_image_pad)
	
	
	        		Z, X, Y = sitk.GetArrayFromImage(transformed_channel_image).shape
	        		pad_x = (self.factor - X % self.factor) % self.factor
	        		pad_y = (self.factor - Y % self.factor) % self.factor
	        		if pad_x > 0 or pad_y > 0:
	        			out_np = np.pad(sitk.GetArrayFromImage(transformed_channel_image), ((0,0), (0,pad_x), (0,pad_y)), mode='edge')
	        			Z, X, Y = out_np.shape  # mettre à jour après padding
	        		else:
		        		out_np = sitk.GetArrayFromImage(transformed_channel_image)
	
	        		# Potential binning
	        		out_np = out_np.reshape(Z, X//self.factor, self.factor, Y//self.factor, self.factor).mean(axis=(2,4))
	        		out_np = out_np.astype(np.uint8)
	
	        		output_path = os.path.join(output_dir, f"frame_{t:04d}_C{channel+1}.tif")
	        		tif.imwrite(output_path, out_np,imagej=True,resolution=(1/(x*self.factor), 1/(y*self.factor)),metadata=metadata)
	        		self.create_fiji_csv(os.path.join(output_dir, 'infoSize.csv'), num_frames, num_channels, global_size[2])
        		
        # reconstruction with Fiji if information available
        print(f"Processing completed, all file in {self.folder_path} treated")
        if not os.path.exists(config_path):
        	print(f"File {config_path} does not exist. Please create it with path to Fiji executable. Hyperstack were not created.")
        else:
        	fiji_path = None
	
        	with open(config_path, "r") as f:
        		for line in f:
        			line = line.strip()
        			if line.startswith("fiji_path="):
        				fiji_path = line.split("=", 1)[1].strip()
        				
        	if not fiji_path:
        		print(f"Fiji path not found in {config_path}, please check the file structure");
	
        	else: 
        		print("Reconstruction in Fiji starts")
        		macro_path = r"createHyperstack_afterPythonAlign_v1.ijm"
        		cmd = f'"{fiji_path}" --headless "{macro_path}" "input_dir={self.folder_path}"'
        		process = subprocess.Popen(cmd, shell=True)
        		process.wait()  # bloque jusqu'à la fin

        messagebox.showinfo("Info", f"Processing completed, all file in {self.folder_path} treated and reconstructed")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()
