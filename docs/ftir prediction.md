Integration plan for automatic IR functional group identification
Objective: Integrate the functional‐group prediction model from the irchracterizationcnn project into our website so that users can click Identify functional groups on an uploaded IR spectrum and see predicted functional groups highlighted on the plot and listed in a table. Ensure proper attribution to the original authors and datasets.
Background and external sources
The repository at gj475/irchracterizationcnn contains scripts for training and evaluating a convolutional neural network to automatically classify functional groups in IR spectra. It provides:
•	A definition of functional groups using SMARTS strings and corresponding labels (smarts.py). The file defines fg_list_extended and label_names_extended lists mapping 37 functional groups such as alkane, alkene, alcohol, ketone, nitrile etc[1][2].
•	A training/evaluation pipeline described in README.txt: to run the project from scratch you execute nist_scraper.py, sdbs_scraper.py, preprocessing.py, split_data.py, data_augmentation.py, hyperparameter_optimization.py, train_model.py, train_weighted_model.py, optimal_threshold.py and finally evaluation.py[3]. The same document notes that all augmented models were based on the extended list of functional groups and that performance analysis was computed using the 0_extended.h5 model[3].
•	A function optimal_threshold that reshapes input spectra to 600 ×1, loads the trained model ../models/0_model_extended.h5 and computes per‑class probability thresholds[4]. This implies the model expects 600 points representing the mid‑IR spectrum (likely 4000–400 cm⁻¹).
The repository does not include the heavy .h5 model files or the scraped datasets. You will need to download 0_model_extended.h5 and the corresponding optimal threshold pickles from the original authors or train the model yourself following the instructions.
High‑level integration steps
1.	Download the trained model and thresholds
2.	Contact the author or search for 0_extended.h5 and optimal_thresholds.pkl from the irchracterizationcnn project.
3.	Store these in a new directory in our repository, e.g. ml_models/ir_groups/.
4.	Add a Python module to run predictions
5.	Create a file ml/ir_group_classifier.py in our repo with a class IRGroupClassifier.
6.	At initialization:
o	Load the Keras model from 0_model_extended.h5.
o	Load the list of 37 functional groups (label_names_extended from smarts.py) – you can either import this file directly or hard‑code the list using the names defined in smarts.py[1][2].
o	Load per‑class thresholds (a dictionary mapping index→threshold) from the pickle file.
7.	Implement a private method _preprocess(spectrum) that:
a.	Converts wavenumber/absorbance arrays to a fixed grid of 600 evenly spaced points in 4000–400 cm⁻¹ (descending). Use linear interpolation (numpy.interp) and clip missing values. The model expects shape (600,1)[4].
b.	Optionally perform baseline correction (asymmetric least squares or simple spline) and normalize between 0 and 1 (match the training preprocessing).
8.	Implement predict_groups(spectrum) to:
o	Call _preprocess on the input.
o	Pass the 600×1 array to the model’s predict method.
o	Apply the per‑class thresholds: if prob[i] ≥ threshold[i], mark the group as present.
o	Return a list of predictions, each including the functional group name, probability and flagged boolean.
9.	Expose a service endpoint
10.	If our backend is Python (Flask/FastAPI), add a route /api/ir-groups that accepts JSON with arrays of wavenumbers and intensities, calls IRGroupClassifier.predict_groups and returns JSON of predicted groups with probabilities and thresholds.
11.	If our backend is Node.js, create a small Python microservice (e.g. using FastAPI) for IR predictions and call it from Node via HTTP. Alternatively, use child_process.spawn to run a Python script that loads the model and returns results.
12.	Integrate with the front‑end
13.	On the page where spectra are displayed, add a button Identify functional groups.
14.	When clicked, send the current spectral data to /api/ir-groups and await the response.
15.	For each predicted group:
o	Shade the corresponding wavenumber region based on NIST correlation ranges (e.g. carbonyl C=O ~ 1850–1650 cm⁻¹). We already planned ranges in our earlier work; use them here as the rule‑based overlay.
o	Place a small label over the shaded area with the group name and probability.
16.	Update the table beneath the plot to include columns such as Band (cm⁻¹), Range (cm⁻¹), Group, Confidence, Source (ML/Rule/Both) and Notes (similar to the schema provided in earlier responses).
17.	Credit and attribution
18.	In our project’s README or an About page, acknowledge that the functional‑group classifier originates from the open‑source project gj475/irchracterizationcnn. Mention the authors’ names if available and link to the repository.
19.	Note that the original dataset comes from NIST and SDBS; include references to those databases.
20.	Also credit any other sources used for functional group ranges (e.g. NIST Middle‑Range IR Correlation charts).
21.	Environment and dependencies
22.	The irchracterizationcnn project uses Keras with the PlaidML backend. You can instead use TensorFlow/Keras CPU backend if GPU is not required.
23.	Add tensorflow, numpy, scipy, pandas and rdkit to our project’s requirements.txt or Conda environment.
24.	Provide a script (e.g. scripts/fetch_ir_model.sh) that downloads the model file and thresholds from a trusted location.
25.	Testing and validation
26.	Write unit tests for IRGroupClassifier using a handful of spectra with known functional groups.
27.	Compare the model’s predictions with manual assignments from our NIST correlation charts.
28.	Log predictions and probabilities for auditing.
By following these steps, Codex will be able to add automatic IR functional‑group classification to our website while crediting the original authors. Use the smarts.py definitions and the model’s expected input shape from the original project[1][4] as the basis for your implementation.
________________________________________
[1] [2] raw.githubusercontent.com
https://raw.githubusercontent.com/gj475/irchracterizationcnn/main/scripts/smarts.py
[3] irchracterizationcnn/README.txt at main · gj475/irchracterizationcnn · GitHub
https://github.com/gj475/irchracterizationcnn/blob/main/README.txt
[4] raw.githubusercontent.com
https://raw.githubusercontent.com/gj475/irchracterizationcnn/main/scripts/optimal_thresholding.py
