/************ createHyperstack_afterPythonAlign_v1 ************
 * This macro is written to reconstruct as an Hyperstack (with the correct sizes) an Image Sequence created 
 * by Python code/exe interfaceAlign_SaveEachFrame_SubsamplingOption_v*; each subfolder in the given input 
 * directory is named after the original image (+_trFrames_chan*_subSamp*); it contains the aligned z-stack
 * for each time-point, each channel; the dimensions (C,Z,T) are indicated in a CSV file infoSize.csv in the folder
 * (careful to the order xyzct); the number of slices differ from original image since black slices are added to keep
 * all information 
 * 
 * Can be launched in the terminal IF the code createHyperstack_afterPythonAlign_v1 is in Fiji Macros Folder 
 * (if location needed: File > Show Folder > Macros) by:
 * "...\fiji-windows-x64.exe" --headless "createHyperstack_afterPythonAlign_v1.ijm" "input_dir=**" (last \ should be doubled (\\) to be correctly read)
 * 
 * 12/25 by AS MACE, tested on Windows, Fiji 1.54p
 */

directory = "";
arg = getArgument();
if (arg != "") { // launch in terminal
	args = split(arg, "=");
	directory = args[1];
}
else // launch in Fiji
	directory = getDirectory("Choose directory treated with code interfaceAlign_SaveEachFrame_SubsamplingOption_v*_");


filelist = getFileList(directory);
for (i = 0; i < lengthOf(filelist); i++) {
	// subfolders are treated
    if ( File.isDirectory(directory + File.separator + filelist[i]) ) {
    	// only if infoSize.csv exists (gives number of channel/frames/slices
        if( File.exists( directory + File.separator + filelist[i]+"infoSize.csv" ) ){
        	img_saveName = substring(filelist[i],0,indexOf(filelist[i],"_trFrames_chan"))+".tif";
        	// if the image was already reconstructed, it is skipped
        	if( !File.exists(directory + File.separator + filelist[i]+img_saveName) ){
	        	print("Treating "+img_saveName);
	        	
	        	// CSV read as text (tested as a Result table, does not seem to work in headless)
	        	csvPath = directory + File.separator + filelist[i]+"infoSize.csv";
	        	csv = File.openAsString(csvPath);
	            lines = split(csv, "\n");
	            values = split(lines[1], ",");
	            T = parseFloat(values[0]);
	            C = parseFloat(values[1]);
	            Z = parseFloat(values[2]);
	        	
	        	File.openSequence( directory + File.separator + filelist[i] , "virtual");
	        	run("Stack to Hyperstack...", "order=xyzct channels="+C+" slices="+Z+" frames="+T+" display=Color");
	        	print("Saving as "+directory + File.separator + filelist[i]+img_saveName);
	        	saveAs("tiff",directory + File.separator + filelist[i]+img_saveName);
	        }
	        else
				print("Image "+img_saveName+" skipped: already reconstructed");
			run("Close All");
        }
    } 
}

