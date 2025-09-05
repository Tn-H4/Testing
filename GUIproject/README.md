tkinter         # usually comes built-in with Python on Windows/Linux
pillow          # image handling (PIL.Image, ImageTk)
opencv-python   # camera access + saving images
numpy           # math arrays, used by both face_recognition + chatbot

#using for testing, source: https://github.com/NeuralNine/youtube-tutorials/tree/main/AI%20Chatbot%20PyTorch
torch           # PyTorch, used for chatbot model
nltk            # tokenization + lemmatization for chatbot

#In Working
#using for testing, source: https://core-electronics.com.au/guides/raspberry-pi/face-recognition-with-raspberry-pi-and-opencv/
imutils         # scanning dataset for training encodings
face-recognition  # face detection + encoding (depends on dlib)

!!!current install needed:
pip install pillow opencv-python imutils face-recognition torch nltk numpy

!!!for usb camera, change index=1 in camera.py, line 11