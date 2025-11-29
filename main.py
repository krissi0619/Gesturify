# spotify_gesture_control.py
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import subprocess
import time
import webbrowser

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

class SpotifyController:
    def __init__(self):
        self.is_spotify_open = False
        
    def open_spotify(self):
        """Open Spotify in browser or focus if already open"""
        try:
            # Try to find and focus existing Spotify window
            spotify_windows = pyautogui.getWindowsWithTitle('Spotify')
            if spotify_windows:
                spotify_windows[0].activate()
                print("🎵 Spotify focused")
                self.is_spotify_open = True
                return True
                
            # If no Spotify window found, open in browser
            print("🌐 Opening Spotify in browser...")
            webbrowser.open('https://open.spotify.com')
            self.is_spotify_open = True
            print("✅ Spotify opened in browser")
            return True
            
        except Exception as e:
            print(f"❌ Failed to open Spotify: {e}")
            return False
    
    def next_track(self):
        """Skip to next track"""
        pyautogui.press('nexttrack')
        print("▶️ Next track")
    
    def previous_track(self):
        """Go to previous track"""
        pyautogui.press('prevtrack')
        print("◀️ Previous track")
    
    def play_pause(self):
        """Toggle play/pause"""
        pyautogui.press('playpause')
        print("⏯️ Play/Pause")
    
    def volume_up(self):
        """Increase volume"""
        pyautogui.press('volumeup')
        print("🔊 Volume up")
    
    def volume_down(self):
        """Decrease volume"""
        pyautogui.press('volumedown')
        print("🔉 Volume down")
    
    def mute_unmute(self):
        """Toggle mute"""
        pyautogui.press('volumemute')
        print("🔇 Mute/Unmute")
    
    def like_track(self):
        """Like current track (Ctrl+L in Spotify Web)"""
        try:
            pyautogui.hotkey('ctrl', 'l')
            print("💚 Liked track")
        except:
            print("❌ Could not like track")
    
    def shuffle(self):
        """Toggle shuffle (Ctrl+S in Spotify Web)"""
        try:
            pyautogui.hotkey('ctrl', 's')
            print("🔀 Shuffle toggled")
        except:
            print("❌ Could not toggle shuffle")

class GestureDetector:
    def __init__(self):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
    
    def get_finger_state(self, landmarks):
        """Get state of each finger (1 = extended, 0 = folded)"""
        fingers = []
        
        # Thumb (compare x-coordinates)
        thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]
        fingers.append(1 if thumb_tip.x < thumb_ip.x else 0)
        
        # Four fingers (compare y-coordinates)
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_pips = [6, 10, 14, 18]  # PIP joints
        
        for tip, pip in zip(finger_tips, finger_pips):
            fingers.append(1 if landmarks[tip].y < landmarks[pip].y else 0)
        
        return fingers
    
    def detect_gesture(self, landmarks):
        """Detect specific hand gestures"""
        if not landmarks:
            return None
        
        fingers = self.get_finger_state(landmarks)
        
        # Thumbs Up 👍 (Only thumb extended)
        if fingers[0] == 1 and sum(fingers[1:]) == 0:
            return "thumbs_up"
        
        # Thumbs Down 👎 (Only thumb folded)
        if fingers[0] == 0 and sum(fingers[1:]) == 0:
            return "thumbs_down"
        
        # Three Fingers 🤟 (Index, Middle, Ring extended)
        if sum(fingers[1:4]) == 3 and fingers[4] == 0:
            return "three_fingers"
        
        # Four Fingers ✋ (All four fingers extended)
        if sum(fingers[1:]) == 4:
            return "four_fingers"
        
        # Victory ✌️ (Index and Middle extended only)
        if fingers[1] == 1 and fingers[2] == 1 and sum(fingers[3:]) == 0 and fingers[0] == 0:
            return "victory"
        
        # Index Up ☝️ (Only index finger extended)
        if fingers[1] == 1 and sum(fingers[2:]) == 0 and fingers[0] == 0:
            return "index_up"
        
        # Index Down 👇 (Only index finger folded, others extended)
        if fingers[1] == 0 and sum(fingers[2:]) == 3 and fingers[0] == 1:
            return "index_down"
        
        # Rock 🤘 (Index and Pinky extended)
        if fingers[1] == 1 and fingers[4] == 1 and sum(fingers[2:4]) == 0 and fingers[0] == 0:
            return "rock"
        
        # OK 👌 (Thumb and Index touching)
        thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
        if distance < 0.05 and sum(fingers[2:]) == 0:
            return "ok"
        
        return None

class GestureControlApp:
    def __init__(self):
        self.gesture_detector = GestureDetector()
        self.spotify_controller = SpotifyController()
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("❌ Error: Could not access webcam")
            exit(1)
        
        # Gesture control settings
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.5  # seconds
        self.current_gesture = None
        
        # Gesture to action mapping
        self.gesture_actions = {
            'thumbs_up': self.spotify_controller.next_track,        # 👍 → Next Track
            'thumbs_down': self.spotify_controller.previous_track,  # 👎 → Previous Track
            'three_fingers': self.spotify_controller.play_pause,    # 🤟 → Play/Pause
            'four_fingers': self.spotify_controller.open_spotify,   # ✋ → Open Spotify
            'victory': self.spotify_controller.mute_unmute,         # ✌️ → Mute/Unmute
            'index_up': self.spotify_controller.volume_up,          # ☝️ → Volume Up
            'index_down': self.spotify_controller.volume_down,      # 👇 → Volume Down
            'rock': self.spotify_controller.like_track,             # 🤘 → Like Track
            'ok': self.spotify_controller.shuffle,                  # 👌 → Toggle Shuffle
        }
    
    def execute_gesture(self, gesture):
        """Execute action for detected gesture with cooldown"""
        current_time = time.time()
        
        # Check cooldown
        if (current_time - self.last_gesture_time) < self.gesture_cooldown:
            return False
        
        # Execute action if gesture is mapped
        if gesture in self.gesture_actions:
            try:
                self.gesture_actions[gesture]()
                self.last_gesture_time = current_time
                return True
            except Exception as e:
                print(f"❌ Error executing {gesture}: {e}")
                return False
        
        return False
    
    def draw_interface(self, image, gesture, executed):
        """Draw UI elements on the camera feed"""
        height, width = image.shape[:2]
        
        # Display current gesture
        color = (0, 255, 0) if executed else (0, 0, 255)  # Green if executed, red if on cooldown
        cv2.putText(image, f"Gesture: {gesture or 'None'}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Display cooldown timer
        cooldown_left = max(0, self.gesture_cooldown - (time.time() - self.last_gesture_time))
        cv2.putText(image, f"Cooldown: {cooldown_left:.1f}s", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Display Spotify status
        status = "🟢 READY" if self.spotify_controller.is_spotify_open else "🟡 OPEN SPOTIFY"
        cv2.putText(image, f"Spotify: {status}", (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw control guide at bottom
        controls = [
            "👍=Next  👎=Prev  🤟=Play/Pause  ✋=Open Spotify",
            "✌️=Mute  ☝️=Vol+  👇=Vol-  🤘=Like  👌=Shuffle"
        ]
        
        for i, text in enumerate(controls):
            y_pos = height - 60 + (i * 30)
            cv2.putText(image, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw quit instruction
        cv2.putText(image, "Press 'Q' to quit", (width - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return image
    
    def run(self):
        """Main application loop"""
        print("🎵 Spotify Gesture Control System")
        print("=" * 50)
        print("👋 GESTURE CONTROLS:")
        print("   👍 Thumbs Up     → Next Track")
        print("   👎 Thumbs Down   → Previous Track")  
        print("   🤟 Three Fingers → Play/Pause")
        print("   ✋ Four Fingers  → Open Spotify")
        print("   ✌️ Victory       → Mute/Unmute")
        print("   ☝️ Index Up      → Volume Up")
        print("   👇 Index Down    → Volume Down")
        print("   🤘 Rock Sign     → Like Track")
        print("   👌 OK Sign       → Toggle Shuffle")
        print("\n💡 TIPS:")
        print("   - Make clear gestures in good lighting")
        print("   - Keep hand visible in camera frame")
        print("   - Wait for cooldown between gestures")
        print("   - Open Spotify first with ✋ gesture")
        print("=" * 50)
        
        while True:
            # Read camera frame
            success, frame = self.cap.read()
            if not success:
                print("❌ Failed to capture frame")
                break
            
            # Mirror the frame for intuitive control
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process hand landmarks
            results = self.gesture_detector.hands.process(rgb_frame)
            gesture_detected = None
            gesture_executed = False
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # Detect gesture
                    gesture = self.gesture_detector.detect_gesture(hand_landmarks.landmark)
                    if gesture:
                        gesture_detected = gesture
                        gesture_executed = self.execute_gesture(gesture)
                        break
            
            # Update interface
            frame = self.draw_interface(frame, gesture_detected, gesture_executed)
            
            # Display frame
            cv2.imshow('Spotify Gesture Control', frame)
            
            # Check for quit command
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord('r') or key == ord('R'):
                print("🔄 Resetting...")
                self.last_gesture_time = 0
            elif key == ord('s') or key == ord('S'):
                print("🎵 Manually opening Spotify...")
                self.spotify_controller.open_spotify()
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        print("👋 Spotify Gesture Control stopped. Thank you for using!")

def main():
    """Main function with error handling"""
    try:
        app = GestureControlApp()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Program interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Ensure cleanup
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()