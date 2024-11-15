import cv2
import base64
import ollama

def capture_and_analyze_image():
    # Initialize camera (try different indices if 0 doesn't work)
    camera = cv2.VideoCapture(1)
    
    # Check if camera opened successfully
    if not camera.isOpened():
        print("Error: Could not open camera")
        return
    
    # Capture a single frame
    ret, frame = camera.read()
    
    # Release the camera
    camera.release()
    
    if not ret:
        print("Error: Could not capture image")
        return
    
    # Rotate the frame 180 degrees due to the document camera's orientation
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    
    # Save frame to temporary file
    temp_image_path = "temp_capture.jpg"
    cv2.imwrite(temp_image_path, frame)
    
    # Convert image to base64
    with open(temp_image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Send to Ollama
    response = ollama.chat(
        model='llama3.2-vision', 
        messages=[{
            'role': 'user',
            'content': 'What do you see in this image?',
            'images': [base64_image]
        }]
    )
    
    print("AI Description:", response['message']['content'])

if __name__ == "__main__":
    capture_and_analyze_image()