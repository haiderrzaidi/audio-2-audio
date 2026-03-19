# #!/bin/bash

# export PYTHON_PATH="./src:${PYTHONPATH}"

# python src/examples/example.py


#!/bin/bash

# Create and activate the Conda environment
# echo "Creating and activating Conda environment..."
# conda create -n speech_env python=3.11 -y
# conda activate speech_env

# Install ffmpeg and portaudio using Conda
echo "Installing ffmpeg and portaudio..."
conda install -c conda-forge ffmpeg portaudio -y

# Install requirements from requirements.txt
echo "Installing requirements..."
pip install -r requirements.txt

# Download the weights
echo "Downloading weights..."
wget https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip -O checkpoints_1226.zip

# Unzip the weights
echo "Unzipping weights..."
unzip checkpoints_1226.zip -d checkpoints_1226

# Copy the folder inside the unzipped folder to the current directory
echo "Copying folder..."
cp -r checkpoints_1226/* .

# Delete the unzipped folder
echo "Cleaning up..."
rm -rf checkpoints_1226

# Download the Vosk model
echo "Downloading Vosk model..."
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip -O vosk-model-en-us-0.22.zip

# Unzip the Vosk model
echo "Unzipping Vosk model..."
unzip vosk-model-en-us-0.22.zip

# Run the Python script
echo "Running Python script..."
python3 .gradio_backend_TM.py
