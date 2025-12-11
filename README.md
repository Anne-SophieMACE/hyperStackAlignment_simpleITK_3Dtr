# hyperStackAlignment_simpleITK_3Dtr

This code was used in the chapter **“Imaging monocyte dynamics within living tumor explants”** of the Methods in Molecular Biology book *Live Imaging of Immune Cells*.  

**Algorithm information:** 3D translation estimation using SimpleITK with the Mean Squares metric and the Regular Step Gradient Descent optimizer.

## License
This project is subject to a specific license from the **Institut Curie**.  
Please refer to the file `Logiciel hyperStackAlignment_simpleITK_3Dtr.licence` for more details.

*******************************************

Ce projet est soumis à une licence spécifique à l'**Institut Curie**.  
Consultez le fichier `Logiciel hyperStackAlignment_simpleITK_3Dtr.licence` pour plus de détails.

## Installation

1. **Create a dedicated environment** (tested with Python 3.12.0):
```python -m venv env3D_transfo```
2. **Activate the environment** (tested on Windows, with Anaconda Power Prompt):
```env3D_transfo\Scripts\activate.bat```
3. **Install the requirements** (replace absolutePathToFolderWithRequirements with the actual path):
```pip install -r absolutePathToFolderWithRequirements/requirements_hyperStackAlignment_simpleITK_3Dtr.txt```
4. **Run the code** (replace absolutePathToFolderWithPythonCode with the actual path):
```python absolutePathToFolderWithPythonCode/hyperStackAlignment_simpleITK_3Dtr_v1.py```

Note: An executable file has also been created for flexible use using PyInstaller (https://pyinstaller.org/en/stable/)
.



