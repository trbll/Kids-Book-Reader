import cv2
import base64
import ollama
from openai import OpenAI
from prompts import READER_STORY_TEXT_EXTRACTION_MESSAGES
from keys import OPENAI_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
from elevenlabs import Voice, play
from elevenlabs.client import ElevenLabs

openai_client = OpenAI(api_key=OPENAI_API_KEY)
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def capture_image():
    """Capture an image from the document camera and return the processed frame"""
    # Initialize camera (try different indices if 0 doesn't work)
    camera = cv2.VideoCapture(1)
    
    # Check if camera opened successfully
    if not camera.isOpened():
        print("Error: Could not open camera")
        return None
    
    # Capture a single frame
    ret, frame = camera.read()
    
    # Release the camera
    camera.release()
    
    if not ret:
        print("Error: Could not capture image") 
        return None
        
    # Rotate the frame 180 degrees due to the document camera's orientation
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    return frame

def encode_frame_to_base64(frame):
    """Convert an OpenCV frame to base64 string"""
    # Encode frame to jpg format
    _, buffer = cv2.imencode('.jpg', frame)
    # Convert to base64
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return base64_image

def analyze_image_ollama(frame):
    """Analyze the given image frame using Ollama vision model"""
    if frame is None:
        return None
        
    # Convert frame to base64
    base64_image = encode_frame_to_base64(frame)

    READER_STORY_TEXT_EXTRACTION_MESSAGES.append(
        {
            'role': 'user',
            'content': 'Here is the next page of the book. Please return ONLY the story text in the image. DO NOT CONTINUE OR EXTRAPOLATE FROM THE TEXT YOU FOUND. JUST RETURN THE TEXT! No commentary before or after the text, either.',
            'images': [base64_image]
        }
    )
    
    # Send to Ollama
    response = ollama.chat(
        model='llama3.2-vision:90b',
        messages=READER_STORY_TEXT_EXTRACTION_MESSAGES
    )

    extracted_text = response['message']['content']

    READER_STORY_TEXT_EXTRACTION_MESSAGES.pop()

    # READER_STORY_TEXT_EXTRACTION_MESSAGES.append(
    #     {
    #         'role': 'assistant',
    #         'content': extracted_text
    #     }
    # )

    return extracted_text

def analyze_image_openai(frame):
    """Analyze the given image frame using OpenAI vision model"""
    print("Analyzing image...")

    if frame is None:
        return None
        
    # Convert frame to base64
    base64_image = encode_frame_to_base64(frame)

    READER_STORY_TEXT_EXTRACTION_MESSAGES.append(
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': 'Here is the next page of the book. Please return ONLY the story text in the image. DO NOT CONTINUE OR EXTRAPOLATE FROM THE TEXT YOU FOUND. JUST RETURN THE TEXT! No commentary before or after the text, either.'
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    )
    
    # Send to OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=READER_STORY_TEXT_EXTRACTION_MESSAGES,
    )

    extracted_text = response.choices[0].message.content

    READER_STORY_TEXT_EXTRACTION_MESSAGES.pop()

    return extracted_text

def generate_speech(text):
    """Generate and play speech from the given text using ElevenLabs"""
    print("Generating speech...")
    try:
        audio = eleven_client.generate(
            text=text,
            voice=Voice(voice_id=ELEVENLABS_VOICE_ID),
            model="eleven_turbo_v2_5"
        )
        play(audio)
    except Exception as e:
        print(f"Error generating speech: {e}")

def main():
    """Main function to coordinate image capture and analysis"""
    print("Press SPACE to capture and analyze the next page. Press 'q' to quit.")
    
    # Create a window to catch keypresses
    cv2.namedWindow('Press SPACE to capture, Q to quit', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Press SPACE to capture, Q to quit', 640, 480)
    
    # Initialize camera and show preview
    camera = cv2.VideoCapture(1)
    
    while True:
        # Show camera preview
        ret, preview = camera.read()
        if ret:
            preview = cv2.rotate(preview, cv2.ROTATE_180)
            cv2.imshow('Press SPACE to capture, Q to quit', preview)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Space bar pressed
            
            # frame = capture_image()
            frame = preview

            if frame is not None:
                description = analyze_image_openai(frame)
                if description:
                    print("\nText from page:", description)
                    generate_speech(description)  # Generate and play speech
                    print("\nPress SPACE for next page or 'q' to quit.")

        elif key == ord('q'):  # Q pressed
            break
    
    # Cleanup
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()